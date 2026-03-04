# 🛡️ Aegis-Hotspot Vault

**Author**: Aryaditya Deshmukh  
**Registration Number**: 23BCE5056  

A secure, offline-first, encrypted file transfer mechanism over a localized Wi-Fi hotspot, built for reliable and completely isolated data transfers.

## Problem Statement

Traditional localized file sharing solutions (like FTP) are fast but natively transmit data in cleartext. In untrusted or deeply restricted offline environments—such as public hotspots or air-gapped field operations—this cleartext vulnerability allows malicious actors on the same LAN to intercept, read, or tamper with the files during transit. 

Aegis-Hotspot Vault mitigates this by applying a hybrid, offline cryptographic architecture bridging the speed of symmetric encryption with the trustless security of asymmetric handshakes.

## Technical Architecture

The core security is implemented through `crypto_engine.py`, leveraging the `PyCryptodome` library:

1. **RSA-2048 (Key Exchange)**: The client (phone) generates a private/public key pair securely. The laptop server uses the public key to encrypt a randomized AES session key. This ensures the Zero-Knowledge principle—even if intercepted, the session key cannot be extracted without the client's localized private key.
2. **AES-256-GCM (Authenticated Encryption)**: The actual file payload is encrypted using the blazing-fast AES-256 block cipher. AES-GCM (Galois/Counter Mode) acts as an **Integrity Guard**, attaching a 16-byte Authentication Tag. If any man-in-the-middle alters a single bit of the file, the GCM tag fails verification and the client abruptly halts the decryption process.

## Setup Instructions

### 1. Laptop Setup (Windows Hotspot + Python Server)
1. Turn on the "Mobile Hotspot" feature on your Windows laptop.
2. Ensure you have Python installed, then install the required dependencies:
   ```bash
   pip install pycryptodome pyftpdlib streamlit
   ```
3. Generate the keypairs and run the localized server:
   ```bash
   python vault_server.py
   ```
   *This hosts the FTP-based secure vault on `0.0.0.0:2121`.*

*(Optional) Launch the Real-Time Cryptographic Dashboard:*
   ```bash
   streamlit run app_visualizer.py
   ```

### 2. Mobile Phone Setup (Termux Client)
1. Connect to the laptop's Wi-Fi Hotspot.
2. Open Termux and run the automated bash setup script, which handles the package upgrades and Git cloning:
   ```bash
   # Transfer the setup_termux.sh to the phone manually or via a quick HTTP server first
   chmod +x setup_termux.sh
   ./setup_termux.sh
   ```
3. Securely transfer your newly generated `private.pem` (from the laptop) to the root folder of the Termux environment.
4. Execute the secure fetch block:
   ```bash
   python vault_client.py secret_document.vault
   ```
