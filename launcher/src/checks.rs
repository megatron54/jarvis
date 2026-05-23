use colored::*;
use which::which;

/// Verify all required dependencies are installed.
/// Returns true if all checks pass.
pub fn verify_all() -> bool {
    let mut all_ok = true;

    all_ok &= check_binary("docker", "Docker");
    all_ok &= check_binary("ollama", "Ollama");
    all_ok &= check_binary("python", "Python 3.11+") || check_binary("python3", "Python 3.11+");

    // Check Docker is running
    if all_ok {
        all_ok &= check_docker_running();
    }

    // Check Ollama is running
    if which("ollama").is_ok() {
        all_ok &= check_ollama_running();
    }

    all_ok
}

fn check_binary(name: &str, display: &str) -> bool {
    match which(name) {
        Ok(path) => {
            println!("  {} {} ({})", "✓".green(), display, path.display().to_string().dimmed());
            true
        }
        Err(_) => {
            println!("  {} {} - {}", "✗".red(), display, "NOT FOUND".red());
            false
        }
    }
}

fn check_docker_running() -> bool {
    let output = std::process::Command::new("docker")
        .args(["info"])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status();

    match output {
        Ok(status) if status.success() => {
            println!("  {} {}", "✓".green(), "Docker daemon running");
            true
        }
        _ => {
            println!("  {} {} - {}", "✗".red(), "Docker daemon", "NOT RUNNING".red());
            println!("    → Start Docker Desktop or run: sudo systemctl start docker");
            false
        }
    }
}

fn check_ollama_running() -> bool {
    // Try to connect to Ollama
    let resp = reqwest::blocking::Client::new()
        .get("http://localhost:11434/api/tags")
        .timeout(std::time::Duration::from_secs(3))
        .send();

    match resp {
        Ok(r) if r.status().is_success() => {
            println!("  {} {}", "✓".green(), "Ollama server running");
            true
        }
        _ => {
            println!("  {} {} - starting...", "!".yellow(), "Ollama server");
            // Try to start Ollama
            #[cfg(target_os = "windows")]
            {
                std::process::Command::new("cmd")
                    .args(["/C", "start", "/B", "ollama", "serve"])
                    .spawn()
                    .ok();
            }
            #[cfg(not(target_os = "windows"))]
            {
                std::process::Command::new("ollama")
                    .arg("serve")
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null())
                    .spawn()
                    .ok();
            }
            // Wait a bit for it to start
            std::thread::sleep(std::time::Duration::from_secs(3));

            let resp2 = reqwest::blocking::Client::new()
                .get("http://localhost:11434/api/tags")
                .timeout(std::time::Duration::from_secs(5))
                .send();

            match resp2 {
                Ok(r) if r.status().is_success() => {
                    println!("  {} {}", "✓".green(), "Ollama started successfully");
                    true
                }
                _ => {
                    println!("  {} {}", "✗".red(), "Could not start Ollama. Run 'ollama serve' manually.");
                    false
                }
            }
        }
    }
}
