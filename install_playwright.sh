#!/bin/bash

# --- Playwright Installation Script for Linux ---
# This script automates the installation of Playwright and its dependencies on a Linux system.

echo "Starting Playwright installation for Linux..."

# 1. Check for Node.js and npm
echo "Checking for Node.js and npm..."
if ! command -v node &> /dev/null
then
    echo "Node.js not found. Installing Node.js (LTS version) using nvm..."
    # Install nvm (Node Version Manager)
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
    # Source nvm to make it available in the current session
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

    # Install the latest LTS version of Node.js
    nvm install --lts
    nvm use --lts
    echo "Node.js installed: $(node -v)"
    echo "npm installed: $(npm -v)"
else
    echo "Node.js already installed: $(node -v)"
    echo "npm already installed: $(npm -v)"
fi

# Ensure npm is up-to-date
echo "Updating npm..."
npm install -g npm@latest

# 2. Install Playwright globally
echo "Installing Playwright globally..."
npm install -g playwright

# 3. Install Playwright browser dependencies
echo "Installing Playwright browser dependencies (Chromium, Firefox, WebKit)..."
playwright install

# 4. Install Playwright specific browser dependencies
echo "Installing Playwright specific browser dependencies..."
playwright install-deps

echo "----------------------------------------------------"
echo "Playwright installation complete!"
echo "To verify the installation, you can run:"
echo "playwright --version"
echo "You can now create a new Playwright project or use it in an existing one."
echo "----------------------------------------------------"

echo "----------------------------------------------------"
echo "Let Start Our telegram Bot!"
echo "you need to check or edit config.py:"
echo "ModsBots"
echo "----------------------------------------------------"
