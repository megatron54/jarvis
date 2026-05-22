#!/bin/bash
# Download recommended models for Jarvis
# Hardware: i5-13600KF + RTX 4060 Ti 16GB + 32GB RAM

set -e

echo "=== Downloading Jarvis models ==="

# Main chat model (10GB VRAM)
echo "[1/5] Downloading qwen2.5:14b-instruct-q4_K_M..."
ollama pull qwen2.5:14b-instruct-q4_K_M

# Fast model for routing and quick tasks (2.5GB VRAM)
echo "[2/5] Downloading qwen2.5:3b..."
ollama pull qwen2.5:3b

# Coding model (5GB VRAM)
echo "[3/5] Downloading qwen2.5-coder:7b-instruct-q4_K_M..."
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Embedding model
echo "[4/5] Downloading nomic-embed-text..."
ollama pull nomic-embed-text

# Reasoning model (swap with main when needed)
echo "[5/5] Downloading deepseek-r1:14b..."
ollama pull deepseek-r1:14b

echo ""
echo "=== All models downloaded ==="
echo "Total VRAM usage (one model at a time):"
echo "  - qwen2.5:14b  → ~10GB"
echo "  - qwen2.5:3b   → ~2.5GB"
echo "  - coder:7b     → ~5GB"
echo "  - deepseek:14b → ~10GB"
echo ""
echo "Your RTX 4060 Ti 16GB can run any single model comfortably."
