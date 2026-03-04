<div align="center">

```
 █████╗ ███████╗ ██████╗ ██╗███████╗
██╔══██╗██╔════╝██╔════╝ ██║██╔════╝
███████║█████╗  ██║  ███╗██║███████╗
██╔══██║██╔══╝  ██║   ██║██║╚════██║
██║  ██║███████╗╚██████╔╝██║███████║
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝
     H O T S P O T   V A U L T
```

**RSA-2048 · AES-256-GCM · Offline-First Secure Bubble**

*Encrypt on your laptop. Transfer over hotspot. Decrypt on Android. Zero internet. Zero trust required.*

---

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![PyCryptodome](https://img.shields.io/badge/PyCryptodome-AES--256--GCM-4CAF50?style=flat-square)](https://pycryptodome.readthedocs.io)
[![pyftpdlib](https://img.shields.io/badge/pyftpdlib-FTP%20Server-0078D4?style=flat-square)](https://pyftpdlib.readthedocs.io)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-FF9800?style=flat-square)](.)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](.)

**[Aryaditya Deshmukh](https://github.com/aryadityad/) · Reg: 23BCE5056 · VIT Chennai**

</div>

---

## Table of Contents

1. [Project Overview](#-project-overview)
2. [Motivation & Use Case](#-motivation--use-case)
3. [System Architecture](#-system-architecture)
4. [Cryptographic Design](#-cryptographic-design)
5. [Vault File Format](#-vault-file-format)
6. [Repository Structure](#-repository-structure)
7. [Component Breakdown](#-component-breakdown)
8. [Quick Start](#-quick-start)
9. [Detailed Setup Guide](#-detailed-setup-guide)
10. [Termux Mobile Setup](#-termux-mobile-setup)
11. [CLI Reference](#-cli-reference)
12. [Configuration](#-configuration)
13. [Security Analysis](#-security-analysis)
14. [Threat Model](#-threat-model)
15. [Dependencies](#-dependencies)
16. [Known Limitations](#-known-limitations)
17. [Future Improvements](#-future-improvements)
18. [Academic Context](#-academic-context)

---

## Project Overview

**Aegis Hotspot Vault** is a cryptographically hardened, offline-first file transfer system. It establishes a **"Secure Bubble"** — a private, air-gapped-style network using a laptop's Wi-Fi hotspot — to securely transfer files to an Android device running Termux.

No cloud. No internet relay. No plaintext on the wire.

Every file is sealed inside a `.vault` container using a **hybrid encryption scheme**: RSA-2048 asymmetric encryption wraps a randomly generated AES-256-GCM session key, which encrypts the actual file content with authenticated encryption. The vault is then served over a local FTP server accessible only within the hotspot subnet.

---

## Motivation & Use Case

### The Problem
Conventional file transfer methods — email, cloud storage, Bluetooth — all involve either a third-party server, plaintext transmission, or weak link-layer encryption. For sensitive documents, this is unacceptable.

### The Solution
Aegis creates an ephemeral, self-contained secure network:

```
  Internet ──────────────── BLOCKED
                                │
  ┌─────────────────────────────▼─────────────────────────────┐
  │                    SECURE BUBBLE                           │
  │                                                           │
  │   Laptop  ←──── Wi-Fi Hotspot ────→  Android Phone        │
  │  (Server)       192.168.137.x        (Termux Client)      │
  │                                                           │
  └───────────────────────────────────────────────────────────┘
```

### Who Is This For?
- Students and researchers transferring sensitive academic documents
- Professionals sharing confidential files in field environments
- Security enthusiasts learning applied cryptography
- Anyone who needs verifiable end-to-end encryption without trusting a third party

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      LAPTOP  (Host)                          │
│                                                              │
│  ┌──────────────┐   encrypt_file()   ┌───────────────────┐  │
│  │   app.py     │──────────────────▶│  crypto_core.py   │  │
│  │  Streamlit   │                    │                   │  │
│  │  Dashboard   │◀── progress_cb() ──│  RSA-2048 OAEP   │  │
│  │              │                    │  AES-256-GCM      │  │
│  │  • Upload    │                    │  Vault Assembly   │  │
│  │  • Pipeline  │                    └────────┬──────────┘  │
│  │  • Hex Log   │                             │ .vault      │
│  └──────────────┘                    ┌────────▼──────────┐  │
│                                      │   shared_vault/   │  │
│                                      │   directory       │  │
│                                      └────────┬──────────┘  │
│  ┌──────────────┐                             │             │
│  │  server.py   │◀────────────────────────────┘             │
│  │  pyftpdlib   │                                           │
│  │  :2121       │                                           │
│  └──────┬───────┘                                           │
└─────────┼────────────────────────────────────────────────────┘
          │  Wi-Fi Hotspot  192.168.137.0/24
          │  FTP (port 2121)
┌─────────▼────────────────────────────────────────────────────┐
│                   ANDROID  (Termux Client)                   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  client.py                                           │   │
│  │  1. FTP connect → 192.168.137.1:2121                 │   │
│  │  2. List & select .vault files                       │   │
│  │  3. Stream download with progress bar                │   │
│  │  4. Parse vault header → extract original filename   │   │
│  │  5. RSA OAEP unwrap → recover AES session key        │   │
│  │  6. AES-256-GCM decrypt + verify 128-bit auth tag    │   │
│  │  7. Save with original filename and extension        │   │
│  │  8. Prompt → termux-open                             │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## Cryptographic Design

Aegis uses a **hybrid encryption scheme**, combining the security guarantees of asymmetric RSA with the performance of symmetric AES.

### Why Hybrid Encryption?

| Algorithm | Strength | Weakness |
|-----------|----------|----------|
| RSA-2048 alone | Strong key exchange | Too slow for large files |
| AES-256 alone | Very fast | Key distribution problem |
| **RSA + AES (hybrid)** | **Best of both** | **None at this scale** |

### Encryption Flow

```
┌─────────────┐
│  Plaintext  │
│   File      │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────┐
│  Stage 1 — KEY GEN                               │
│  Generate random 256-bit AES session key         │
│  os.urandom(32)  →  aes_key                      │
└──────────────────┬───────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────┐
│  Stage 2 — RSA WRAP                              │
│  Encrypt aes_key with recipient's RSA public key │
│  PKCS1_OAEP.encrypt(aes_key)  →  wrapped_key     │
│  Output: 256 bytes                               │
└──────────────────┬───────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────┐
│  Stage 3 — AES-256-GCM ENCRYPT                   │
│  Encrypt file with session key                   │
│  AES.new(aes_key, MODE_GCM, nonce=nonce)         │
│  encrypt_and_digest(plaintext)                   │
│  Output: ciphertext + 128-bit auth tag           │
└──────────────────┬───────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────┐
│  Stage 4 — VAULT ASSEMBLY                        │
│  Concatenate all components → .vault file        │
└──────────────────────────────────────────────────┘
```

### Algorithm Specifications

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| RSA key size | 2048 bits | NIST recommended minimum through 2030 |
| RSA padding | PKCS1-OAEP (SHA-1) | Semantically secure; resists chosen-ciphertext attacks |
| AES key size | 256 bits | Maximum AES security level |
| AES mode | GCM (Galois/Counter Mode) | Authenticated encryption — confidentiality + integrity |
| Nonce size | 128 bits (16 bytes) | Full GCM nonce width |
| Auth tag size | 128 bits (16 bytes) | Maximum GCM tag length |
| RNG | `Crypto.Random.get_random_bytes` | Cryptographically secure PRNG |

---

## Vault File Format

The `.vault` binary format is purpose-built for this project:

```
Offset    Size        Field               Description
──────    ────        ─────               ───────────
0         8 bytes     Magic               ASCII "AEGISVLT" — file identifier
8         1 byte      Version             Format version (0x01)
9         2 bytes     Filename Length     Big-endian uint16 — original filename length
11        N bytes     Original Filename   UTF-8 encoded (e.g. "report.pdf")
11+N      256 bytes   Wrapped AES Key     RSA-2048 OAEP encrypted AES-256 session key
267+N     16 bytes    Nonce               AES-GCM nonce (random, unique per file)
283+N     16 bytes    Auth Tag            GCM authentication tag (128-bit)
299+N     variable    Ciphertext          AES-256-GCM encrypted file content
```

**Total fixed overhead per vault:** `8 + 1 + 2 + 256 + 16 + 16 = 299 bytes` + filename length

This compact, self-describing format ensures the vault is fully self-contained — the receiver needs only `private.pem` and `client.py` to recover the original file with its correct name and extension, with no out-of-band metadata required.

---

## Repository Structure

```
aegis-hotspot-vault/
│
├── crypto_core.py       Cryptographic engine
│                        RSA-2048 OAEP + AES-256-GCM
│                        Vault format read/write
│                        Progress callback hooks for UI
│                        Standalone CLI interface
│
├── app.py               Streamlit web dashboard
│                        Drag-and-drop file uploader
│                        Animated 4-stage pipeline visualizer
│                        Live hex inspector (key, nonce, tag)
│                        Vault metrics panel
│                        Sidebar RSA key management
│
├── server.py            pyftpdlib FTP server
│                        Binds to 0.0.0.0:2121
│                        Serves ./shared_vault/
│                        Full session audit logging
│
├── client.py            Termux Android client
│                        FTP download with ASCII progress bar
│                        Full RSA-AES vault decryption
│                        Original filename restoration
│                        termux-open integration
│
├── requirements.txt     Python package dependencies with versions
├── .gitignore           Strictly blocks *.pem and *.vault from git
└── README.md            This file
```

---

## Component Breakdown

### `crypto_core.py` — The Cryptographic Engine

The heart of the project. Implements all cryptographic operations using **PyCryptodome**.

**Key functions:**

```python
generate_rsa_keypair(key_dir)
# Generates RSA-2048 keypair, saves public.pem + private.pem
# Returns: (public_key_path, private_key_path)

encrypt_file(plaintext_path, public_key_path, output_dir, progress_cb)
# Full 4-stage encryption pipeline with optional UI callback
# Returns: (vault_path, metadata_dict)
# metadata: aes_key_hex, rsa_pub_hex, nonce_hex, tag_hex, sizes

decrypt_vault(vault_path, private_key_path, output_dir)
# Parses vault, RSA-unwraps AES key, GCM-decrypts and verifies
# Returns: path to recovered plaintext file
```

The `progress_cb(stage_name)` callback is fired at the start of each stage (`KEY_GEN`, `RSA_WRAP`, `AES_ENCRYPT`, `VAULT_ASSEMBLY`), allowing `app.py` to animate the pipeline in real time.

---

### `app.py` — Streamlit Real-Time Dashboard

A dark-themed web UI that makes the cryptographic pipeline visible and educational.

**Pipeline stage animation:**

```
[ KEY_GEN ] → [ RSA_WRAP ] → [ AES_ENCRYPT ] → [ VAULT_ASSEMBLY ]
  pending        pending          pending             pending
     ↓ run clicked
  active         pending          pending             pending
     ↓
  done ✔        active           pending             pending
     ↓
  done ✔        done ✔          active              pending
     ↓
  done ✔        done ✔          done ✔             done ✔
```

**Live Hex Inspector** displays:
- AES-256 session key (32 bytes, full hex)
- RSA-2048 public modulus (truncated to 48 bytes for display)
- GCM nonce (16 bytes)
- GCM auth tag (16 bytes)

---

### `server.py` — Localized FTP Server

```
Host    : 0.0.0.0  (reachable from any hotspot client)
Port    : 2121     (non-privileged, no root needed)
User    : aryaditya
Pass    : 5056
Serves  : ./shared_vault/
```

Subclasses `FTPHandler` with a custom `AuditHandler` that logs every connect, login attempt, file transfer, and logout with timestamp and source IP.

---

### `client.py` — Termux Android Client

Designed for minimal dependencies and terminal-friendly output. Execution flow:

1. Validate `~/private.pem` exists
2. FTP connect to `192.168.137.1:2121`
3. List `.vault` files — auto-select if only one
4. Stream download with real-time ASCII progress bar
5. Parse vault binary header → extract embedded original filename
6. RSA-OAEP unwrap AES session key using private key
7. AES-256-GCM decrypt + verify auth tag (raises on tamper)
8. Write file with original name and extension
9. Prompt `Open file now? [Y/N]` → `termux-open` on Y

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/aryadityad/aegis-hotspot-vault.git
cd aegis-hotspot-vault

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate RSA keypair
python crypto_core.py genkeys

# 4. Terminal 1 — Start FTP server
python server.py

# 5. Terminal 2 — Launch dashboard
python -m streamlit run app.py
# Open http://localhost:8501
```

---

## Detailed Setup Guide

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | 3.10 minimum |
| pip | latest | `python -m pip install --upgrade pip` |
| Windows | 10/11 | For Mobile Hotspot feature |
| Android | 8.0+ | For Termux compatibility |

### Step 1 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Generate RSA Keypair

```bash
python crypto_core.py genkeys --dir .
```

Produces:
```
public.pem    ← safe to keep in project (used to encrypt)
private.pem   ← SECRET — transfer to phone, never commit to git
```

> **Warning:** `private.pem` is your only decryption key. Back it up securely. It is blocked from git by `.gitignore`.

### Step 3 — Enable Windows Mobile Hotspot

```
Settings → Network & Internet → Mobile Hotspot → ON
```

Hotspot gateway IP: `192.168.137.1`. Connect your Android to this network.

### Step 4 — Start FTP Server

```bash
python server.py
```

### Step 5 — Launch Dashboard

```bash
python -m streamlit run app.py
```

Visit `http://localhost:8501`. Use the sidebar to confirm the public key path, then drag and drop a file and click **Vault It!**

---

## Termux Mobile Setup

### Install Termux

Get it from [F-Droid](https://f-droid.org/packages/com.termux/) (recommended — Play Store version is outdated).

### Install Python and PyCryptodome

```bash
pkg update && pkg upgrade -y
pkg install python -y
pip install pycryptodome
```

### Grant Storage Access

```bash
termux-setup-storage
# Tap ALLOW when prompted
```

### Transfer Files via USB

Connect phone in **File Transfer (MTP)** mode. Copy `private.pem` and `client.py` to phone Downloads, then:

```bash
cp ~/storage/downloads/private.pem ~/private.pem
cp ~/storage/downloads/client.py ~/client.py
```

### Run the Client

Make sure the laptop hotspot is active and your phone is connected to it, then:

```bash
python client.py
```

The client will connect, list available vaults, let you select one, download it, decrypt it, restore the original filename, and offer to open it immediately.

---

## CLI Reference

```bash
# Generate RSA-2048 keypair
python crypto_core.py genkeys
python crypto_core.py genkeys --dir /path/to/keystore

# Encrypt a file (headless, no Streamlit)
python crypto_core.py encrypt secret.pdf
python crypto_core.py encrypt secret.pdf --pub public.pem --outdir ./shared_vault

# Decrypt a vault file
python crypto_core.py decrypt secret.vault
python crypto_core.py decrypt secret.vault --priv private.pem --outdir ./recovered
```

---

## Configuration

### `server.py`

```python
HOST          = "0.0.0.0"            # Bind to all interfaces
PORT          = 2121                  # FTP port
VAULT_DIR     = "./shared_vault"      # Served directory
FTP_USER      = "aryaditya"           # FTP username
FTP_PASS      = "5056"                # FTP password
PASSIVE_PORTS = range(60000, 60100)   # Passive mode port range
```

### `client.py`

```python
SERVER_IP     = "192.168.137.1"                        # Hotspot gateway
SERVER_PORT   = 2121                                   # Match server.py
FTP_USER      = "aryaditya"                            # Match server.py
FTP_PASS      = "5056"                                 # Match server.py
PRIV_KEY_PATH = os.path.expanduser("~/private.pem")   # RSA private key
OUTPUT_DIR    = os.path.expanduser("~/storage/downloads/aegis_out")
```

---

## Security Analysis

### What Is Protected

| Attack Vector | Protection Mechanism |
|---------------|---------------------|
| Wi-Fi eavesdropping | AES-256-GCM — ciphertext indistinguishable from random |
| In-transit tampering | 128-bit GCM auth tag — any modification causes decryption failure |
| AES key extraction from vault | RSA-2048 OAEP — requires factoring a 2048-bit semiprime |
| AES brute force | 2²⁵⁶ keyspace — computationally infeasible |
| Replay / vault reuse | Per-file random 128-bit nonce — every vault is cryptographically unique |
| Accidental key commit | `.gitignore` blocks all `*.pem` files |

### What Is Not Protected

- FTP credentials are plaintext (FTP protocol limitation — no TLS in this build)
- File transfer metadata (filename, timing, size) is visible to network observers
- Private key security depends entirely on physical device security
- No brute-force protection on the FTP server

---

## Threat Model

**Adversary:** A passive observer with full packet capture on the hotspot subnet (e.g., another device connected to the same hotspot).

**Capability:** Can capture the complete FTP session, including the `.vault` file contents and FTP credentials.

**Outcome:** The adversary obtains the vault binary. Without `private.pem`, the RSA-wrapped AES key cannot be recovered and the ciphertext cannot be decrypted. The vault contents remain computationally secure.

**Out of scope:** Physical device compromise, malware on either device, side-channel attacks on the cryptographic implementation, compromise of the RSA private key itself.

---

## Dependencies

| Package | Version | License | Used In |
|---------|---------|---------|---------|
| `pycryptodome` | ≥ 3.20.0 | BSD-2-Clause | All components |
| `streamlit` | ≥ 1.35.0 | Apache 2.0 | `app.py` (laptop only) |
| `pyftpdlib` | ≥ 1.5.9 | MIT | `server.py` (laptop only) |

Termux mobile only requires `pycryptodome` — no Streamlit or pyftpdlib needed on the phone.

---

## Known Limitations

1. **Single recipient** — vault is encrypted to one RSA public key; multi-recipient would require wrapping the AES key separately for each recipient
2. **No TLS on FTP** — vault filename and credentials are visible in network captures; file content remains encrypted
3. **Static gateway IP** — `192.168.137.1` is the Windows hotspot default; Linux may differ
4. **In-memory GCM** — very large files are loaded fully into RAM before encryption; not suitable for multi-GB files without chunking
5. **No key revocation** — compromised keypair has no invalidation mechanism for existing vaults

---

## Future Improvements

- [ ] TLS on FTP (`pyftpdlib` supports `TLS_FTPHandler`)
- [ ] Multi-recipient vaults (wrap AES key to N public keys)
- [ ] QR code key transfer (eliminate USB dependency)
- [ ] Streaming AES-GCM for large files (chunked encryption)
- [ ] HMAC over vault header for metadata integrity
- [ ] Termux:Widget one-tap shortcut for vault retrieval
- [ ] Web decryption UI using the WebCrypto API

---

## Academic Context

Developed for the **Cryptography and Network Security (CNS)** course at **VIT Chennai**.

**Concepts demonstrated:**

- Hybrid encryption (asymmetric key transport + symmetric data encryption)
- Authenticated Encryption with Associated Data (AEAD) via AES-GCM
- RSA-OAEP padding and its semantic security guarantees over textbook RSA
- Galois/Counter Mode: how GCM combines CTR-mode encryption with a Galois field MAC
- Practical key management: generation, storage, secure transport, and access control
- Local network security: building a controlled, isolated communication channel
- Binary file format design for cryptographic containers

---

<div align="center">

---

**Aegis Hotspot Vault** — Built for learning. Designed for security.

[Aryaditya Deshmukh](https://github.com/aryadityad/) · 23BCE5056 · VIT Chennai

*"The best encryption is the kind you understand."*

---

</div>