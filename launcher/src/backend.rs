use colored::*;
use std::process::{Command, Stdio};
use std::time::Duration;
use std::thread;
use std::fs;

use crate::get_project_dir;

static BACKEND_PID_FILE: &str = ".jarvis_backend.pid";

pub fn start() {
    let project_dir = get_project_dir();
    let pid_file = project_dir.join(BACKEND_PID_FILE);

    // Check if already running
    if is_running() {
        println!("  {} Backend already running", "✓".green());
        return;
    }

    // Ensure Python dependencies are installed
    ensure_dependencies(&project_dir);

    // Start the backend with uvicorn
    let child = Command::new("python")
        .args(["-m", "uvicorn", "jarvis.main:app", "--host", "0.0.0.0", "--port", "8080"])
        .current_dir(&project_dir)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .env("PYTHONPATH", project_dir.join("src").to_str().unwrap_or("src"))
        .spawn();

    match child {
        Ok(c) => {
            fs::write(&pid_file, c.id().to_string()).ok();
            println!("  {} Backend starting (PID: {})", "✓".green(), c.id());
        }
        Err(e) => {
            // Try python3
            let child2 = Command::new("python3")
                .args(["-m", "uvicorn", "jarvis.main:app", "--host", "0.0.0.0", "--port", "8080"])
                .current_dir(&project_dir)
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .env("PYTHONPATH", project_dir.join("src").to_str().unwrap_or("src"))
                .spawn();

            match child2 {
                Ok(c) => {
                    fs::write(&pid_file, c.id().to_string()).ok();
                    println!("  {} Backend starting (PID: {})", "✓".green(), c.id());
                }
                Err(_) => {
                    eprintln!("  {} Could not start backend: {}", "✗".red(), e);
                }
            }
        }
    }
}

pub fn wait_ready() {
    let client = reqwest::blocking::Client::new();

    for _ in 0..40 {
        thread::sleep(Duration::from_millis(500));
        let resp = client
            .get("http://localhost:8080/health")
            .timeout(Duration::from_secs(2))
            .send();

        if let Ok(r) = resp {
            if r.status().is_success() {
                return;
            }
        }
    }
    println!("  {} Backend may not be fully ready (continuing anyway)", "!".yellow());
}

pub fn stop() {
    let project_dir = get_project_dir();
    let pid_file = project_dir.join(BACKEND_PID_FILE);

    if let Ok(pid_str) = fs::read_to_string(&pid_file) {
        if let Ok(pid) = pid_str.trim().parse::<u32>() {
            #[cfg(target_os = "windows")]
            {
                Command::new("taskkill")
                    .args(["/PID", &pid.to_string(), "/F"])
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .status()
                    .ok();
            }
            #[cfg(not(target_os = "windows"))]
            {
                Command::new("kill")
                    .arg(pid.to_string())
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .status()
                    .ok();
            }
        }
        fs::remove_file(&pid_file).ok();
    }
    println!("  {} Backend stopped", "✓".green());
}

pub fn is_running() -> bool {
    let client = reqwest::blocking::Client::new();
    client
        .get("http://localhost:8080/health")
        .timeout(Duration::from_secs(2))
        .send()
        .map(|r| r.status().is_success())
        .unwrap_or(false)
}

pub fn print_status() {
    println!("{}", "Backend:".bold());
    if is_running() {
        println!("  {} API running at http://localhost:8080", "●".green());
    } else {
        println!("  {} API not running", "●".red());
    }
}

fn ensure_dependencies(project_dir: &std::path::Path) {
    // Check if jarvis is importable
    let check = Command::new("python")
        .args(["-c", "import jarvis"])
        .env("PYTHONPATH", project_dir.join("src").to_str().unwrap_or("src"))
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();

    let needs_install = match check {
        Ok(s) => !s.success(),
        Err(_) => true,
    };

    if needs_install {
        println!("  {} Installing Python dependencies (first run)...", "!".yellow());
        let status = Command::new("pip")
            .args(["install", "-e", "."])
            .current_dir(project_dir)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();

        match status {
            Ok(s) if s.success() => {
                println!("  {} Dependencies installed", "✓".green());
            }
            _ => {
                eprintln!("  {} Failed to install dependencies. Run manually: pip install -e .", "✗".red());
            }
        }
    }
}
