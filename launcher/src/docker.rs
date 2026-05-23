use colored::*;
use indicatif::{ProgressBar, ProgressStyle};
use std::process::Command;
use std::time::Duration;
use std::thread;

use crate::get_project_dir;

pub fn start_services() -> bool {
    let project_dir = get_project_dir();

    let status = Command::new("docker")
        .args(["compose", "up", "-d", "postgres", "redis", "chromadb"])
        .current_dir(&project_dir)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::piped())
        .status();

    match status {
        Ok(s) if s.success() => {
            println!("  {} Docker services started", "✓".green());
            true
        }
        _ => {
            eprintln!("  {} Failed to start Docker services", "✗".red());
            false
        }
    }
}

pub fn stop_services() {
    let project_dir = get_project_dir();
    Command::new("docker")
        .args(["compose", "down"])
        .current_dir(&project_dir)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .ok();
    println!("  {} Docker services stopped", "✓".green());
}

pub fn wait_healthy() {
    let pb = ProgressBar::new_spinner();
    pb.set_style(
        ProgressStyle::default_spinner()
            .template("  {spinner:.cyan} Waiting for services to be healthy...")
            .unwrap(),
    );

    for _ in 0..30 {
        pb.tick();
        thread::sleep(Duration::from_secs(1));

        if is_postgres_ready() && is_redis_ready() {
            pb.finish_with_message(format!("  {} All services healthy", "✓".green()));
            return;
        }
    }

    pb.finish_with_message(format!("  {} Services may not be fully ready", "!".yellow()));
}

fn is_postgres_ready() -> bool {
    Command::new("docker")
        .args(["exec", "jarvis-postgres", "pg_isready", "-U", "jarvis"])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

fn is_redis_ready() -> bool {
    Command::new("docker")
        .args(["exec", "jarvis-redis", "redis-cli", "ping"])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

pub fn print_status() {
    println!("{}", "Docker Services:".bold());
    let project_dir = get_project_dir();
    let output = Command::new("docker")
        .args(["compose", "ps", "--format", "table {{.Name}}\t{{.Status}}"])
        .current_dir(&project_dir)
        .output();

    match output {
        Ok(out) => {
            let text = String::from_utf8_lossy(&out.stdout);
            for line in text.lines() {
                if line.contains("Up") || line.contains("running") {
                    println!("  {} {}", "●".green(), line);
                } else if line.contains("Exit") {
                    println!("  {} {}", "●".red(), line);
                } else {
                    println!("  {}", line.dimmed());
                }
            }
        }
        Err(_) => println!("  {}", "Could not get Docker status".red()),
    }
}
