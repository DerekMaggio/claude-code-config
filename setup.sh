#!/usr/bin/env bash
set -euo pipefail

# Setup script for claude-code-config dependencies
#
# Installs all required tools for working with this repo:
#   - Node.js (via nvm), Claude Code, Gemini CLI
#   - gh, uv, jq, gron, yq, git-gtr
#   - Optionally: Salesforce CLI (sf)
#
# Usage:
#   ./setup.sh                 # install all (prompts for optional tools)
#   ./setup.sh --skip-optional # install required tools only
#
# Skips any tool that is already installed.
# Requires: curl, git, sudo

INSTALL_DIR="/usr/local/bin"
SKIP_OPTIONAL=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-optional) SKIP_OPTIONAL=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Detect architecture
case "$(uname -m)" in
    x86_64)  ARCH="amd64" ;;
    aarch64) ARCH="arm64" ;;
    armv7l)  ARCH="armv7" ;;
    *)       echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac

echo "=== claude-code-config dependency installer ==="
echo ""

# --- Helper ---
check_installed() {
    if command -v "$1" &>/dev/null; then
        echo "[SKIP] $1 is already installed: $("$1" --version 2>/dev/null | head -1)"
        return 0
    fi
    return 1
}

# --- Node.js via nvm ---
install_node() {
    if check_installed node; then return; fi
    echo "[INSTALL] Node.js via nvm"

    set +eu
    if ! command -v nvm &>/dev/null; then
        echo "  Installing nvm..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        # shellcheck source=/dev/null
        [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    fi

    nvm install --lts
    nvm use --lts
    set -eu
    echo "[OK] node installed: $(node --version 2>&1)"
}

# --- GitHub CLI (gh) ---
install_gh() {
    if check_installed gh; then return; fi
    echo "[INSTALL] GitHub CLI (gh)"

    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=${ARCH} signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq gh
    echo "[OK] gh installed: $(gh --version 2>&1 | head -1)"
}

# --- uv ---
install_uv() {
    if check_installed uv; then return; fi
    echo "[INSTALL] uv (Python package manager)"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "[OK] uv installed: $(uv --version 2>&1 | head -1)"
}

# --- jq ---
install_jq() {
    if check_installed jq; then return; fi
    echo "[INSTALL] jq (JSON processor)"
    sudo apt-get update -qq
    sudo apt-get install -y -qq jq
    echo "[OK] jq installed: $(jq --version 2>&1 | head -1)"
}

# --- gron ---
install_gron() {
    if check_installed gron; then return; fi
    echo "[INSTALL] gron (JSON flattener)"

    local tmp
    tmp=$(mktemp -d)
    local url
    url=$(curl -sL -o /dev/null -w '%{url_effective}' https://github.com/tomnomnom/gron/releases/latest)
    local version="${url##*/}"

    curl -sL "https://github.com/tomnomnom/gron/releases/download/${version}/gron-linux-${ARCH}-${version#v}.tgz" \
        | tar xz -C "$tmp"
    sudo install -m 755 "$tmp/gron" "$INSTALL_DIR/gron"
    rm -rf "$tmp"
    echo "[OK] gron installed: $(gron --version 2>&1 | head -1)"
}

# --- yq ---
install_yq() {
    if check_installed yq; then return; fi
    echo "[INSTALL] yq (YAML processor)"

    local url
    url=$(curl -sL -o /dev/null -w '%{url_effective}' https://github.com/mikefarah/yq/releases/latest)
    local version="${url##*/}"

    sudo curl -sL "https://github.com/mikefarah/yq/releases/download/${version}/yq_linux_${ARCH}" \
        -o "$INSTALL_DIR/yq"
    sudo chmod +x "$INSTALL_DIR/yq"
    echo "[OK] yq installed: $(yq --version 2>&1 | head -1)"
}

# --- Claude Code ---
install_claude_code() {
    if check_installed claude; then return; fi
    echo "[INSTALL] Claude Code"
    npm install --global @anthropic-ai/claude-code
    echo "[OK] claude installed: $(claude --version 2>&1 | head -1)"
}

# --- Gemini CLI ---
install_gemini() {
    if check_installed gemini; then return; fi
    echo "[INSTALL] Gemini CLI"
    npm install --global @google/gemini-cli
    echo "[OK] gemini installed: $(gemini --version 2>&1 | head -1)"
}

# --- git-worktree-runner (git-gtr) ---
install_gtr() {
    if check_installed git-gtr; then return; fi
    echo "[INSTALL] git-worktree-runner (git-gtr)"

    git clone https://github.com/coderabbitai/git-worktree-runner.git "$INSTALL_DIR/git-worktree-runner"
    (cd "$INSTALL_DIR/git-worktree-runner" && sudo ./install.sh)
    echo "[OK] git-gtr installed"
}

# --- Run required installs ---
install_node
install_claude_code
install_gemini
install_gh
install_uv
install_jq
install_gron
install_yq
install_gtr

# --- Optional: Salesforce CLI ---
if [[ "$SKIP_OPTIONAL" == false ]]; then
    echo ""
    read -rp "Install Salesforce CLI (sf)? Only needed for monthly-customer-scheduling. [y/N] " install_sf
    if [[ "${install_sf,,}" == "y" ]]; then
        if check_installed sf; then
            :
        else
            echo "[INSTALL] Salesforce CLI (sf)"
            npm install --global @salesforce/cli
            echo "[OK] sf installed: $(sf --version 2>&1 | head -1)"
            echo ""
            echo "  NOTE: You still need to authenticate:"
            echo "    sf org login web --alias \$salesforce_org_alias  # set in config/devops.json"
        fi
    fi
fi

echo ""
echo "=== Claude Code symlinks ==="
bash "$(dirname "${BASH_SOURCE[0]}")/helper_scripts/update_symlinks.sh"

echo ""
echo "=== Setup complete ==="
echo ""

# --- Verification ---
echo "Dependency verification:"
for cmd in git python3 node npm claude gemini gh jq uv xdg-open docker gron yq git-gtr; do
    if command -v "$cmd" &>/dev/null; then
        printf "  %-12s ✓\n" "$cmd"
    else
        printf "  %-12s ✗ MISSING\n" "$cmd"
    fi
done

if command -v sf &>/dev/null; then
    printf "  %-12s ✓ (optional)\n" "sf"
else
    printf "  %-12s - not installed (optional)\n" "sf"
fi
