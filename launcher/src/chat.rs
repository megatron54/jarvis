use colored::*;
use std::io::{self, Write};
use std::time::Duration;

/// Start interactive chat session by communicating with the backend API.
pub fn start_interactive(model: Option<String>) {
    println!("{}", "┌─────────────────────────────────────────┐".cyan());
    println!("{}", "│  JARVIS - Type 'exit' to quit           │".cyan());
    println!("{}", "│  Commands: /clear /status /model <name> │".cyan());
    println!("{}", "└─────────────────────────────────────────┘".cyan());
    println!();

    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(120))
        .build()
        .expect("Failed to create HTTP client");

    let session_id = format!("cli-{}", std::process::id());
    let mut _current_model = model;

    loop {
        print!("{} ", "You →".green().bold());
        io::stdout().flush().unwrap();

        let mut input = String::new();
        if io::stdin().read_line(&mut input).is_err() {
            break;
        }

        let input = input.trim();
        if input.is_empty() {
            continue;
        }

        // Handle commands
        match input {
            "exit" | "/exit" | "/quit" => break,
            "/clear" => {
                println!("{}", "Conversation cleared.".dimmed());
                continue;
            }
            "/status" => {
                print_chat_status(&client);
                continue;
            }
            s if s.starts_with("/model ") => {
                _current_model = Some(s[7..].to_string());
                println!("{} {}", "Model set to:".dimmed(), _current_model.as_ref().unwrap().cyan());
                continue;
            }
            _ => {}
        }

        // Send to API
        let body = serde_json::json!({
            "role": "user",
            "content": input,
            "session_id": session_id,
        });

        print!("\n{} ", "Jarvis →".cyan().bold());
        io::stdout().flush().unwrap();

        // Use streaming endpoint
        let resp = client
            .post("http://localhost:8080/api/v1/chat/stream")
            .json(&body)
            .send();

        match resp {
            Ok(response) if response.status().is_success() => {
                let reader = response.text().unwrap_or_default();
                print!("{}", reader);
                println!("\n");
            }
            Ok(_) => {
                // Fallback to non-streaming
                let resp2 = client
                    .post("http://localhost:8080/api/v1/chat")
                    .json(&body)
                    .send();

                match resp2 {
                    Ok(r) => {
                        if let Ok(data) = r.json::<serde_json::Value>() {
                            let content = data["content"].as_str().unwrap_or("No response");
                            println!("{}\n", content);
                        }
                    }
                    Err(e) => {
                        println!("{}\n", format!("Error: {}", e).red());
                    }
                }
            }
            Err(e) => {
                println!("{}", format!("Connection error: {}. Is the backend running?", e).red());
                println!("{}\n", "Run 'jarvis up' to start all services.".dimmed());
            }
        }
    }

    println!("\n{}", "Goodbye!".dimmed());
}

fn print_chat_status(client: &reqwest::blocking::Client) {
    match client.get("http://localhost:8080/health").send() {
        Ok(r) => {
            if let Ok(data) = r.json::<serde_json::Value>() {
                println!("{}: {}", "Status".bold(), data["status"].as_str().unwrap_or("unknown"));
                if let Some(services) = data["services"].as_object() {
                    for (name, status) in services {
                        let s = status.as_str().unwrap_or("unknown");
                        let indicator = if s == "up" { "✓".green() } else { "✗".red() };
                        println!("  {} {}: {}", indicator, name, s);
                    }
                }
            }
        }
        Err(_) => println!("{}", "Backend not reachable".red()),
    }
    println!();
}
