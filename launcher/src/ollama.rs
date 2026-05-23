use colored::*;
use indicatif::{ProgressBar, ProgressStyle};
use std::process::Command;
use std::time::Duration;

const REQUIRED_MODELS: &[&str] = &[
    "qwen2.5:14b-instruct-q4_K_M",
    "qwen2.5:3b",
    "nomic-embed-text",
];

const OPTIONAL_MODELS: &[&str] = &[
    "qwen2.5-coder:7b-instruct-q4_K_M",
    "deepseek-r1:14b",
];

pub fn ensure_models() {
    let installed = get_installed_models();

    let mut missing: Vec<&str> = Vec::new();
    for model in REQUIRED_MODELS {
        if installed.iter().any(|m| m.starts_with(model.split(':').next().unwrap_or(model))) {
            println!("  {} {} installed", "✓".green(), model);
        } else {
            println!("  {} {} missing", "!".yellow(), model);
            missing.push(model);
        }
    }

    if !missing.is_empty() {
        println!("\n  Pulling {} missing model(s)...", missing.len());
        for model in &missing {
            pull_model(model);
        }
    }
}

pub fn pull_all_models() {
    println!("{}", "Pulling all models (required + optional)...".cyan());
    for model in REQUIRED_MODELS.iter().chain(OPTIONAL_MODELS.iter()) {
        pull_model(model);
    }
    println!("\n{}", "All models ready!".green().bold());
}

fn pull_model(model: &str) {
    let pb = ProgressBar::new_spinner();
    pb.set_style(
        ProgressStyle::default_spinner()
            .template(&format!("  {{spinner:.cyan}} Pulling {}...", model))
            .unwrap(),
    );
    pb.enable_steady_tick(Duration::from_millis(100));

    let status = Command::new("ollama")
        .args(["pull", model])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status();

    match status {
        Ok(s) if s.success() => {
            pb.finish_with_message(format!("  {} {} pulled", "✓".green(), model));
        }
        _ => {
            pb.finish_with_message(format!("  {} Failed to pull {}", "✗".red(), model));
        }
    }
}

fn get_installed_models() -> Vec<String> {
    let output = Command::new("ollama")
        .args(["list"])
        .output();

    match output {
        Ok(out) => {
            String::from_utf8_lossy(&out.stdout)
                .lines()
                .skip(1) // skip header
                .filter_map(|line| line.split_whitespace().next().map(String::from))
                .collect()
        }
        Err(_) => Vec::new(),
    }
}

pub fn print_models() {
    println!("{}", "Ollama Models:".bold());
    let models = get_installed_models();
    if models.is_empty() {
        println!("  {}", "No models installed".yellow());
    } else {
        for model in &models {
            let is_required = REQUIRED_MODELS.iter().any(|r| model.contains(r.split(':').next().unwrap_or("")));
            if is_required {
                println!("  {} {}", "●".green(), model);
            } else {
                println!("  {} {}", "○".dimmed(), model);
            }
        }
    }
}
