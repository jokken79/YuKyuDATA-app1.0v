#!/bin/bash
# =============================================================================
# install-hooks.sh - Install pre-commit hooks for YuKyuDATA-app
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=============================================="
echo "  YuKyuDATA-app Pre-commit Hooks Installer"
echo "=============================================="
echo ""

cd "$PROJECT_ROOT"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "ERROR: Not a git repository. Please run from project root."
    exit 1
fi

# Check Python availability
if ! command -v python &> /dev/null; then
    echo "ERROR: Python not found. Please install Python first."
    exit 1
fi

echo "[1/4] Checking pre-commit installation..."

# Install pre-commit if not available
if ! command -v pre-commit &> /dev/null; then
    echo "      Installing pre-commit..."
    pip install pre-commit
else
    echo "      pre-commit already installed: $(pre-commit --version)"
fi

echo "[2/4] Installing git hooks..."
pre-commit install
pre-commit install --hook-type post-commit

echo "[3/4] Making scripts executable..."
chmod +x scripts/check-secrets.sh 2>/dev/null || true
chmod +x scripts/check-memory.sh 2>/dev/null || true
chmod +x scripts/run-checks.sh 2>/dev/null || true

echo "[4/4] Running initial check..."
pre-commit run --all-files || true

echo ""
echo "=============================================="
echo "  Installation complete!"
echo "=============================================="
echo ""
echo "Hooks installed:"
echo "  - pre-commit: Runs before each commit"
echo "  - post-commit: Updates CLAUDE_MEMORY.md"
echo ""
echo "Commands:"
echo "  pre-commit run --all-files  # Run all checks"
echo "  pre-commit run <hook-id>    # Run specific hook"
echo "  git commit --no-verify      # Skip hooks (use sparingly)"
echo ""
