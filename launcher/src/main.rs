use clap::{Parser, Subcommand};
use colored::*;
use std::process::Command;
use std::path::PathBuf;

mod checks;
mod docker;
mod ollama;
mod backend;
mod chat;

#[derive(Parser)]
#[command(name = "jarvis", about = "Jarvis AI Assistant - One command to rule them all")]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand)]
enum Commands {
    /// Start everything and open chat (default)
    Up,
    /// Stop all services
    Down,
    /// Check system status
    Status,
    /// Interactive chat (services must be running)
    Chat {
        /// Model override
        #[arg(short, long)]
        model: Option<String>,
    },
    /// Pull/update all required models
    Models,
    /// Show logs
    Logs,
}

fn main() {
    let cli = Cli::parse();

    let command = cli.command.unwrap_or(Commands::Up);

    match command {
        Commands::Up => cmd_up(),
        Commands::Down => cmd_down(),
        Commands::Status => cmd_status(),
        Commands::Chat { model } => cmd_chat(model),
        Commands::Models => cmd_models(),
        Commands::Logs => cmd_logs(),
    }
}

fn cmd_up() {
    print_banner();

    // 1. Check dependencies
    println!("\n{}", "━━━ Checking dependencies ━━━".cyan().bold());
    if !checks::verify_all() {
        std::process::exit(1);
    }

    // 2. Start Docker services
    println!("\n{}", "━━━ Starting infrastructure ━━━".cyan().bold());
    if !docker::start_services() {
        eprintln!("{}", "Failed to start Docker services".red());
        std::process::exit(1);
    }

    // 3. Wait for services to be healthy
    println!("\n{}", "━━━ Waiting for services ━━━".cyan().bold());
    docker::wait_healthy();

    // 4. Ensure models are available
    println!("\n{}", "━━━ Checking models ━━━".cyan().bold());
    ollama::ensure_models();

    // 5. Start backend
    println!("\n{}", "━━━ Starting Jarvis backend ━━━".cyan().bold());
    backend::start();

    // 6. Wait for backend to be ready
    backend::wait_ready();

    // 7. Launch chat
    println!("\n{}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".green().bold());
    println!("{}", "  Jarvis is ready. Starting chat...".green().bold());
    println!("{}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━".green().bold());
    println!();

    cmd_chat(None);
}

fn cmd_down() {
    println!("{}", "Stopping Jarvis...".yellow());
    backend::stop();
    docker::stop_services();
    println!("{}", "All services stopped.".green());
}

fn cmd_status() {
    print_banner();
    println!();
    checks::verify_all();
    println!();
    docker::print_status();
    println!();
    ollama::print_models();
    println!();
    backend::print_status();
}

fn cmd_chat(model: Option<String>) {
    chat::start_interactive(model);
}

fn cmd_models() {
    ollama::pull_all_models();
}

fn cmd_logs() {
    let project_dir = get_project_dir();
    Command::new("docker")
        .args(["compose", "logs", "-f", "--tail", "50"])
        .current_dir(&project_dir)
        .status()
        .ok();
}

fn print_banner() {
    let banner = r#"
       ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
       ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
       ██║███████║██████╔╝██║   ██║██║███████╗
  ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
  ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
   ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
    "#;
    println!("{}", banner.cyan().bold());
    println!("  {}", "Local AI Personal Assistant v0.3.0".dimmed());
    println!("  {}", "Hardware: i5-13600KF | RTX 4060 Ti 16GB | 32GB RAM".dimmed());
}

pub fn get_project_dir() -> PathBuf {
    // Try to find the project directory
    let candidates = [
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().map(|p| p.to_path_buf()),
        dirs::document_dir().map(|d| d.join("Cortex").join("Proyectos").join("Jarvis")),
        std::env::current_dir().ok(),
    ];

    for candidate in candidates.iter().flatten() {
        if candidate.join("docker-compose.yml").exists() {
            return candidate.clone();
        }
    }

    eprintln!("{}", "Could not find Jarvis project directory!".red());
    std::process::exit(1);
}
