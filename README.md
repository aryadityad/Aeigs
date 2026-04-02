# 🛡️ Aegis Hotspot Vault

### RSA-2048 · AES-256-GCM · Offline-First Secure Bubble

> Encrypt on your laptop. Transfer over hotspot. Decrypt on Android. Zero internet. Zero trust required.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![PyCryptodome](https://img.shields.io/badge/PyCryptodome-AES--256--GCM-4CAF50?style=flat-square)
![pyftpdlib](https://img.shields.io/badge/pyftpdlib-FTP%20Server-0078D4?style=flat-square)
![qrcode](https://img.shields.io/badge/qrcode-Key%20Transfer-9B59B6?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-FF9800?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**[Aryaditya Deshmukh](https://github.com/aryadityad/) · Reg: 23BCE5056 · VIT Chennai**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Motivation & Use Case](#motivation--use-case)
3. [System Architecture](#system-architecture)
4. [Cryptographic Design](#cryptographic-design)
5. [Vault File Format](#vault-file-format)
6. [Repository Structure](#repository-structure)
7. [Component Breakdown](#component-breakdown)
8. [Quick Start](#quick-start)
9. [Detailed Setup Guide](#detailed-setup-guide)
10. [Termux Mobile Setup](#termux-mobile-setup)
11. [QR Key Transfer](#qr-key-transfer)
12. [Auto Network Scanner](#auto-network-scanner)
13. [CLI Reference](#cli-reference)
14. [Configuration](#configuration)
15. [Security Analysis](#security-analysis)
16. [Threat Model](#threat-model)
17. [Dependencies](#dependencies)
18. [Known Limitations](#known-limitations)
19. [Academic Context](#academic-context)

---

## Project Overview

**Aegis Hotspot Vault** is a cryptographically hardened, offline-first file transfer system. It establishes a **"Secure Bubble"** — a private, air-gapped-style network using a laptop's Wi-Fi hotspot — to securely transfer files to an Android device running Termux.

No cloud. No internet relay. No plaintext on the wire.

Every file is sealed inside a `.vault` container using a **hybrid encryption scheme**: RSA-2048 asymmetric encryption wraps a randomly generated AES-256-GCM session key, which encrypts the actual file content with authenticated encryption. The vault is then served over a local FTP server accessible only within the hotspot subnet.

**Key features:**
- One double-click launcher (`launch.bat`) sets up the entire environment automatically
- Live Streamlit dashboard with animated encryption pipeline and hex inspector
- 4-tab UI: Vault a File · How It Works · Cryptography Deep Dive · QR Key Transfer
- Animated terminal UI on Android with live MB/s speed and ETA
- QR code transfer of `private.pem` — no USB needed
- Auto network scanner — detects the laptop IP automatically on the phone

---

## Motivation & Use Case

### The Problem

Conventional file transfer methods — email, cloud storage, Bluetooth — all involve either a third-party server, plaintext transmission, or weak link-layer encryption. For sensitive documents, this is unacceptable.

### The Solution

Aegis creates an ephemeral, self-contained secure network:

```
  Internet ──────────────── BLOCKED
                                │
  ┌─────────────────────────────▼──────────────────────────────┐
  │                      SECURE BUBBLE                         │
  │                                                            │
  │   Laptop  ←──── Wi-Fi Hotspot ────→  Android Phone        │
  │  (Server)        192.168.137.x        (Termux Client)      │
  │                                                            │
  └────────────────────────────────────────────────────────────┘
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
│  ┌──────────────┐    encrypt_file()   ┌──────────────────┐  │
│  │   app.py     │ ─────────────────▶  │ crypto_core.py   │  │
│  │  Streamlit   │                     │                  │  │
│  │  Dashboard   │ ◀── progress_cb() ─ │  RSA-2048 OAEP   │  │
│  │              │                     │  AES-256-GCM     │  │
│  │  4 Tabs:     │                     │  Vault Assembly  │  │
│  │  • Vault     │                     └────────┬─────────┘  │
│  │  • How It    │                              │ .vault     │
│  │  • Crypto    │                     ┌────────▼─────────┐  │
│  │  • QR Key    │                     │  shared_vault/   │  │
│  └──────────────┘                     └────────┬─────────┘  │
│                                                │            │
│  ┌──────────────┐                              │            │
│  │  server.py   │ ◀────────────────────────────┘            │
│  │  FTP :2121   │                                           │
│  └──────┬───────┘                                           │
└─────────┼────────────────────────────────────────────────────┘
          │  Wi-Fi Hotspot · 192.168.137.0/24 · FTP port 2121
┌─────────▼────────────────────────────────────────────────────┐
│                   ANDROID  (Termux Client)                   │
│                                                              │
│  client.py                                                   │
│  1.  Auto-scan subnet  →  find laptop IP                     │
│  2.  FTP connect  →  IP:2121                                 │
│  3.  List & select .vault files                              │
│  4.  Stream download  (live MB/s + ETA progress bar)         │
│  5.  Parse vault header  →  extract original filename        │
│  6.  RSA OAEP unwrap  →  recover AES session key             │
│  7.  AES-256-GCM decrypt  +  verify 128-bit auth tag         │
│  8.  Save with original filename and extension               │
│  9.  Prompt  →  termux-open                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Cryptographic Design

Aegis uses a **hybrid encryption scheme** combining the security of asymmetric RSA with the performance of symmetric AES.

### Why Hybrid Encryption?

| Algorithm | Strength | Weakness |
|-----------|----------|----------|
| RSA-2048 alone | Strong key exchange | Too slow for large files |
| AES-256 alone | Very fast | Key distribution problem |
| **RSA + AES hybrid** | **Best of both** | **None at this scale** |

### Encryption Flow

```
Plaintext File
      │
      ▼
[Stage 1 — KEY GEN]
  Generate random 256-bit AES session key
  get_random_bytes(32)  →  aes_key
      │
      ▼
[Stage 2 — RSA WRAP]
  Encrypt aes_key with recipient's RSA public key
  PKCS1_OAEP.encrypt(aes_key)  →  wrapped_key  (256 bytes)
      │
      ▼
[Stage 3 — AES-256-GCM ENCRYPT]
  AES.new(aes_key, MODE_GCM, nonce=nonce)
  encrypt_and_digest(plaintext)  →  ciphertext + 128-bit auth tag
      │
      ▼
[Stage 4 — VAULT ASSEMBLY]
  Write binary vault file → .vault
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

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 8 bytes | Magic | ASCII `AEGISVLT` — file identifier |
| 8 | 1 byte | Version | Format version `0x01` |
| 9 | 2 bytes | Filename Length | Big-endian uint16 |
| 11 | N bytes | Original Filename | UTF-8 encoded (e.g. `report.pdf`) |
| 11+N | 256 bytes | Wrapped AES Key | RSA-2048 OAEP encrypted AES session key |
| 267+N | 16 bytes | Nonce | AES-GCM nonce, random per file |
| 283+N | 16 bytes | Auth Tag | GCM authentication tag (128-bit) |
| 299+N | variable | Ciphertext | AES-256-GCM encrypted file content |

**Fixed overhead per vault:** 299 bytes + filename length

This self-describing format means the receiver only needs `private.pem` and `client.py` — no out-of-band metadata required.

---

## Repository Structure

```
aegis-hotspot-vault/
│
├── crypto_core.py      Cryptographic engine (RSA + AES, vault read/write, CLI)
├── app.py              Streamlit dashboard (4 tabs, pipeline visualizer, QR key transfer)
├── server.py           pyftpdlib FTP server (0.0.0.0:2121, audit logging)
├── client.py           Termux Android client (auto-scanner, download, decrypt, open)
├── launch.bat          Windows one-click launcher (venv, deps, keys, server, dashboard)
├── requirements.txt    Python dependencies
├── .gitignore          Blocks *.pem and *.vault from git
└── README.md           This file
```

---

## Component Breakdown

### `crypto_core.py` — The Cryptographic Engine

The heart of the project. Implements all cryptographic operations using **PyCryptodome**. Also works as a standalone CLI.

```python
generate_rsa_keypair(key_dir)
# Generates RSA-2048 keypair → public.pem + private.pem

encrypt_file(plaintext_path, public_key_path, output_dir, progress_cb)
# Full 4-stage pipeline. Returns (vault_path, metadata_dict)
# metadata: aes_key_hex, rsa_pub_hex, nonce_hex, tag_hex, sizes

decrypt_vault(vault_path, private_key_path, output_dir)
# Parses vault, unwraps AES key, decrypts and verifies
```

---

### `app.py` — Streamlit Dashboard

A dark-themed, monospace web UI with **4 tabs**:

| Tab | Contents |
|-----|----------|
| 🚀 Vault a File | File uploader with live preview card, animated pipeline, hex inspector, vault metrics |
| 📖 How It Works | System overview, component cards, 3-column transfer flow, security guarantees |
| 🔬 Cryptography Deep Dive | RSA-OAEP + AES-GCM explainers, vault format spec, encrypt/decrypt pseudocode |
| 📲 Key Transfer (QR) | Scannable QR code of `private.pem`, SHA-256 fingerprint, Termux scan instructions |

The **Live Hex Inspector** shows raw hex of the AES session key, RSA modulus, GCM nonce, and auth tag after every encryption run — with inline comments explaining each value.

---

### `server.py` — FTP Server

```
Host   :  0.0.0.0    (all interfaces — reachable over hotspot)
Port   :  2121       (non-privileged, no root required)
User   :  aryaditya
Pass   :  5056
Serves :  ./shared_vault/
```

Custom `AuditHandler` logs every connection, login attempt, file transfer, and logout with timestamp and source IP.

---

### `client.py` — Termux Android Client

Full animated terminal UI with ANSI colours. Key features:

**Auto Network Scanner** — no hardcoded IP needed:
- Scans `192.168.137.x`, `192.168.1.x`, `192.168.0.x`, `10.0.0.x` in parallel (60 threads)
- Finds the laptop in under 2 seconds
- Shows a live `Scanning 192.168.137.1–254 …` spinner while searching
- Set `SERVER_IP = "192.168.137.1"` to skip scanning if the IP is known

**Live Progress Bar** with real-time MB/s speed and ETA countdown.

**Crypto Stage Animator** — 4 stages tick from `⟳` to `✔` as each operation completes.

**Post-decrypt Summary Table** showing file type, size, transfer speed, AES key hex, nonce, and auth tag.

---

### `launch.bat` — Windows Auto Launcher

Double-click to start everything. Steps it runs automatically:

1. `cd /d %~dp0` — always runs from its own folder regardless of where it's launched from
2. Checks Python is installed
3. Creates `venv` if missing
4. Runs `pip install -r requirements.txt --upgrade`
5. Generates RSA keypair if `public.pem` doesn't exist yet
6. Opens FTP server in a titled PowerShell window
7. Opens Streamlit dashboard in a second window with `--server.headless true`
8. Waits 5 seconds then opens `http://localhost:8501` in the browser — exactly once

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/aryadityad/Aeigs.git
cd Aeigs

# 2. Install
pip install -r requirements.txt

# 3. Generate RSA keypair
python crypto_core.py genkeys

# 4. Terminal 1 — FTP server
python server.py

# 5. Terminal 2 — Dashboard
python -m streamlit run app.py
# Visit http://localhost:8501
```

Or on Windows — just double-click **`launch.bat`**.

---

## Detailed Setup Guide

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | 3.10 minimum |
| pip | latest | `python -m pip install --upgrade pip` |
| Windows | 10/11 | For Mobile Hotspot |
| Android | 8.0+ | For Termux |

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
public.pem    ←  safe to keep in project (used to encrypt)
private.pem   ←  SECRET — transfer to phone, never commit to git
```

> ⚠️ `private.pem` is your only decryption key. If lost, all vaults are permanently unrecoverable. Blocked from git by `.gitignore`.

### Step 3 — Enable Windows Mobile Hotspot

```
Settings → Network & Internet → Mobile Hotspot → ON
```

Gateway IP: `192.168.137.1`. Connect your Android to this network.

### Step 4 — Start FTP Server

```bash
python server.py
```

### Step 5 — Launch Dashboard

```bash
python -m streamlit run app.py
```

Visit `http://localhost:8501`. Drag and drop a file and click **Vault It!**

---

## Termux Mobile Setup

### Install Termux

Download from [F-Droid](https://f-droid.org/packages/com.termux/) — recommended over the Play Store version.

### Install Dependencies

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

### Transfer `client.py` and `private.pem`

**Option A — USB (MTP):** Connect phone in File Transfer mode, copy files to Downloads, then:

```bash
cp ~/storage/downloads/private.pem ~/private.pem
cp ~/storage/downloads/client.py ~/client.py
```

**Option B — QR Code:** See [QR Key Transfer](#qr-key-transfer) below — no USB needed.

### Run the Client

```bash
python client.py
```

Expected output:

```
  ╔═══════════════════════════════════════════════════╗
  ║    🛡️  AEGIS HOTSPOT VAULT — SECURE CLIENT    ║
  ║       Aryaditya Deshmukh · 23BCE5056 · VIT       ║
  ╚═══════════════════════════════════════════════════╝

  [1/5]  Checking credentials
  ✔  Private key found  →  ~/private.pem

  [2/5]  Locating Aegis server
  ◆  Scanning 192.168.137.1–254 …
  ✔  Server found  →  192.168.137.1:2121
  ✔  Connected · user=aryaditya

  [3/5]  Scanning vault directory
  ──────────────────────────────────────────────────
  Available Vaults   (1 found)
  [0]  report.vault                          44.2 KB
  ──────────────────────────────────────────────────

  [4/5]  Downloading  →  report.vault
  [████████████████████████████████]  100.0%  1.2 MB/s  ETA 00:00

  [5/5]  Decrypting vault
  ✔  [RSA-OAEP   ]  Unwrapping AES session key
  ✔  [AES-GCM    ]  Decrypting ciphertext
  ✔  [AUTH TAG   ]  Verifying 128-bit authentication tag
  ✔  [ASSEMBLE   ]  Writing file to storage

  ✔  SECURE TRANSFER COMPLETE
  File              report.pdf
  Transfer speed    1.2 MB/s
  Auth tag          8a3b1c2d4e5f6a7b…
```

---

## QR Key Transfer

The **📲 Key Transfer (QR)** tab in the dashboard displays a scannable QR code of `private.pem` — eliminating the need for USB transfer.

### Scan on Termux

```bash
# Install scanner tools
pkg install termux-tools

# Scan QR from screen and save as private key
termux-camera-photo -c 0 qr.jpg
zbarimg qr.jpg > ~/private.pem
```

### Verify the Key Fingerprint

The dashboard shows a SHA-256 fingerprint of the key. After scanning, verify it matches:

```bash
sha256sum ~/private.pem
```

> ⚠️ **Security warning:** The QR code contains your full RSA private key. Only scan it in a private environment. Anyone who photographs the screen can decrypt your vaults.

---

## Auto Network Scanner

`client.py` automatically scans the local subnet to find the laptop's FTP server — no hardcoded IP required.

**How it works:**

1. Scans 4 subnets concurrently: `192.168.137.x`, `192.168.1.x`, `192.168.0.x`, `10.0.0.x`
2. 60 parallel threads, 0.4s timeout per host
3. Returns the first host with port 2121 open
4. Typically finds the server in under 2 seconds

**Skip scanning** (faster if IP is known) — edit the top of `client.py`:

```python
SERVER_IP = "192.168.137.1"   # Set to None to auto-scan
```

**Add custom subnets:**

```python
SCAN_SUBNETS = ["192.168.137", "10.42.0", "172.20.10"]
```

---

## CLI Reference

```bash
# Generate RSA-2048 keypair
python crypto_core.py genkeys
python crypto_core.py genkeys --dir /path/to/keystore

# Encrypt a file (no GUI)
python crypto_core.py encrypt secret.pdf
python crypto_core.py encrypt secret.pdf --pub public.pem --outdir ./shared_vault

# Decrypt a vault
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
SERVER_IP     = None                  # None = auto-scan subnets
SERVER_PORT   = 2121                  # Must match server.py
FTP_USER      = "aryaditya"           # Must match server.py
FTP_PASS      = "5056"                # Must match server.py
PRIV_KEY_PATH = "~/private.pem"       # RSA private key on phone
OUTPUT_DIR    = "~/storage/downloads/aegis_out"
SCAN_SUBNETS  = ["192.168.137", "192.168.1", "192.168.0", "10.0.0"]
SCAN_TIMEOUT  = 0.4                   # Seconds per host
SCAN_WORKERS  = 60                    # Parallel scan threads
```

---

## Security Analysis

### What Is Protected

| Attack Vector | Protection |
|---------------|-----------|
| Wi-Fi eavesdropping | AES-256-GCM — ciphertext indistinguishable from random data |
| In-transit tampering | 128-bit GCM auth tag — any modification causes decryption failure |
| AES key extraction from vault | RSA-2048 OAEP — requires factoring a 2048-bit semiprime |
| AES brute force | 2²⁵⁶ keyspace — computationally infeasible |
| Vault replay / reuse | Per-file random 128-bit nonce — every vault is cryptographically unique |
| Accidental private key commit | `.gitignore` blocks all `*.pem` files |

### What Is Not Protected

- FTP credentials are transmitted in plaintext (FTP protocol limitation)
- File transfer metadata (filename, size, timing) is visible to a network observer
- Private key security depends entirely on physical device security
- No brute-force protection on the FTP login

---

## Threat Model

**Adversary:** A passive observer with full packet capture on the hotspot subnet.

**Capability:** Can capture the complete FTP session including the `.vault` file and FTP credentials.

**Outcome:** The adversary obtains the vault binary. Without `private.pem`, the RSA-wrapped AES key cannot be recovered and the ciphertext cannot be decrypted. Vault contents remain computationally secure.

**Out of scope:** Physical device compromise, malware on either device, side-channel attacks, compromise of the RSA private key itself.

---

## Dependencies

| Package | Version | License | Used In |
|---------|---------|---------|---------|
| `pycryptodome` | ≥ 3.20.0 | BSD-2-Clause | All components |
| `streamlit` | ≥ 1.35.0 | Apache 2.0 | `app.py` (laptop only) |
| `pyftpdlib` | ≥ 1.5.9 | MIT | `server.py` (laptop only) |
| `qrcode[pil]` | ≥ 7.4.2 | MIT | `app.py` QR tab (laptop only) |

Termux only requires `pycryptodome`.

---

## Known Limitations

1. **Single recipient** — vault is encrypted to one RSA public key only
2. **No TLS on FTP** — vault filename and credentials visible in network captures; file content remains encrypted
3. **In-memory processing** — very large files load fully into RAM before encryption
4. **No key revocation** — compromised keypair has no invalidation mechanism for existing vaults
5. **QR transfer size** — very long RSA keys may produce dense QR codes; use a bright screen at full brightness for reliable scanning

---

## Academic Context

Developed for the **Cryptography and Network Security (CNS)** course at **VIT Chennai**.

**Concepts demonstrated:**

- Hybrid encryption (asymmetric key transport + symmetric data encryption)
- Authenticated Encryption with Associated Data (AEAD) via AES-GCM
- RSA-OAEP padding and semantic security over textbook RSA
- Galois/Counter Mode: CTR-mode encryption combined with a Galois field MAC
- Practical key management: generation, secure storage, QR-based transport
- Local network security: subnet scanning, isolated communication channel
- Binary file format design for cryptographic containers

---

*Aegis Hotspot Vault — Built for learning. Designed for security.*

**[Aryaditya Deshmukh](https://github.com/aryadityad/) · 23BCE5056 · VIT Chennai**