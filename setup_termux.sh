#!/bin/bash
# Aegis-Hotspot Vault: Termux Client Setup Script

echo "Starting setup for Aegis-Hotspot Vault in Termux environment..."

# Update and upgrade core packages to ensure system stability
echo "Updating packages..."
pkg update -y && pkg upgrade -y

# Install Git, Python and its package manager
echo "Installing Git, Python and dependencies..."
pkg install git python clang make binutils -y

# Clone the repository (Replace URL with your actual GitHub repository URL after you push)
# Clone the repository (Replace URL with your actual GitHub repository URL after you push)
echo "Cloning the Aegis-Hotspot Vault repository..."
git clone https://github.com/aryadityad/Aeigis.git
cd Aeigis

# Install required Python packages for cryptography
# Note: ftplib is built into the Python Standard Library, so 'pip install ftplib' is not needed!
echo "Installing PyCryptodome (RSA/AES-GCM Security Core)..."
pip install pycryptodome

echo "Setup complete! Termux environment is ready for Aegis-Hotspot Vault."
echo "Ensure your 'private.pem' is in the current directory before running: python vault_client.py <filename>"
