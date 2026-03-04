"""
╔══════════════════════════════════════════════════════════════╗
║         AEGIS-HOTSPOT VAULT — Termux Mobile Client           ║
║         Author : Aryaditya Deshmukh (23BCE5056)              ║
║         Institute: VIT Chennai                               ║
╚══════════════════════════════════════════════════════════════╝

Run on Android / Termux:
    python client.py

Requirements (install inside Termux):
    pkg install python
    pip install pycryptodome

The script:
  1. Connects to the laptop hotspot gateway via FTP.
  2. Lists .vault files available on the server.
  3. Downloads the selected vault to ~/storage/downloads/.
  4. Decrypts it using the bundled RSA private key.
"""

import os
import sys
import ftplib
import logging
from pathlib import Path

from Crypto.PublicKey import RSA
from Crypto.Cipher    import AES, PKCS1_OAEP

# ── Config (edit these if your hotspot IP / creds change) ──────
SERVER_IP   = "192.168.137.1"     # Windows hotspot default gateway
SERVER_PORT = 2121
FTP_USER    = "aryaditya"
FTP_PASS    = "5056"

# Where the private key lives on the phone
PRIV_KEY_PATH = os.path.expanduser("~/private.pem")

# Where decrypted output goes
OUTPUT_DIR  = os.path.expanduser("~/storage/downloads/aegis_out")

# Vault format constants (must match crypto_core.py)
VAULT_MAGIC    = b"AEGISVLT"
RSA_BLOCK_SIZE = 256
NONCE_SIZE     = 16
TAG_SIZE       = 16

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level  = logging.INFO,
    format = "[%(asctime)s] %(levelname)s %(message)s",
    datefmt= "%H:%M:%S",
)
log = logging.getLogger("aegis.client")


# ── Helpers ────────────────────────────────────────────────────

def _progress_bar(transferred: int, total: int, width: int = 40):
    """ASCII progress bar for Termux terminal."""
    pct   = transferred / total if total else 0
    filled = int(width * pct)
    bar   = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r  [{bar}]  {pct*100:5.1f}%  {transferred/1024:.1f} KB")
    sys.stdout.flush()
    if transferred >= total:
        print()


def _decrypt_vault(vault_bytes: bytes, priv_key_path: str) -> bytes:
    """Full RSA-AES vault decryption. Returns plaintext bytes."""
    magic   = vault_bytes[:8]
    if magic != VAULT_MAGIC:
        raise ValueError("Not a valid Aegis vault file.")

    offset        = 9   # magic(8) + version(1)
    fname_len     = int.from_bytes(vault_bytes[offset:offset+2], "big"); offset += 2
    original_name = vault_bytes[offset:offset+fname_len].decode("utf-8"); offset += fname_len
    wrapped_key   = vault_bytes[offset : offset + RSA_BLOCK_SIZE]; offset += RSA_BLOCK_SIZE
    nonce         = vault_bytes[offset : offset + NONCE_SIZE];     offset += NONCE_SIZE
    tag           = vault_bytes[offset : offset + TAG_SIZE];       offset += TAG_SIZE
    ciphertext    = vault_bytes[offset:]

    log.info("Original filename : %s", original_name)

    log.info("Nonce      : %s", nonce.hex())
    log.info("Auth Tag   : %s", tag.hex())

    priv_key   = RSA.import_key(Path(priv_key_path).read_bytes())
    cipher_rsa = PKCS1_OAEP.new(priv_key)
    aes_key    = cipher_rsa.decrypt(wrapped_key)
    log.info("AES key    : %s…", aes_key.hex()[:32])

    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce, mac_len=TAG_SIZE)
    plaintext  = cipher_aes.decrypt_and_verify(ciphertext, tag)
    log.info("GCM auth tag verified ✔")
    return plaintext, original_name


# ── FTP Download ───────────────────────────────────────────────

def list_vaults(ftp: ftplib.FTP) -> list[str]:
    """Return list of .vault filenames on the server."""
    files = ftp.nlst()
    return [f for f in files if f.endswith(".vault")]


def download_vault(ftp: ftplib.FTP, filename: str) -> bytes:
    """Stream-download a vault file with a progress bar."""
    try:
        total = ftp.size(filename)
    except Exception:
        total = 0

    chunks      = []
    transferred = 0

    def _collect(chunk: bytes):
        nonlocal transferred
        chunks.append(chunk)
        transferred += len(chunk)
        if total:
            _progress_bar(transferred, total)

    log.info("Downloading: %s  (%d bytes)", filename, total)
    ftp.retrbinary(f"RETR {filename}", _collect, blocksize=8192)
    return b"".join(chunks)


# ── Main ───────────────────────────────────────────────────────

def main():
    print("\n" + "═" * 52)
    print("   🛡️  AEGIS HOTSPOT VAULT — TERMUX CLIENT")
    print("═" * 52)

    # Check private key
    if not Path(PRIV_KEY_PATH).exists():
        print(f"\n❌  Private key not found at: {PRIV_KEY_PATH}")
        print("    Copy private.pem to your phone and update PRIV_KEY_PATH.")
        sys.exit(1)

    # Connect
    print(f"\n[*] Connecting to {SERVER_IP}:{SERVER_PORT} …")
    try:
        ftp = ftplib.FTP()
        ftp.connect(SERVER_IP, SERVER_PORT, timeout=10)
        ftp.login(FTP_USER, FTP_PASS)
        print(f"[✔] Connected  — {ftp.getwelcome()}")
    except Exception as exc:
        print(f"[✘] FTP connection failed: {exc}")
        sys.exit(1)

    # List vaults
    vaults = list_vaults(ftp)
    if not vaults:
        print("\n[!] No .vault files found on server.")
        ftp.quit()
        sys.exit(0)

    print("\n[*] Available vaults:")
    for i, v in enumerate(vaults):
        print(f"    [{i}] {v}")

    # Select
    if len(vaults) == 1:
        choice = 0
    else:
        try:
            choice = int(input("\n    Select index: "))
        except (ValueError, KeyboardInterrupt):
            print("\n[!] Aborted.")
            ftp.quit()
            sys.exit(0)

    if choice not in range(len(vaults)):
        print("[✘] Invalid selection.")
        ftp.quit()
        sys.exit(1)

    selected = vaults[choice]

    # Download
    print()
    vault_bytes = download_vault(ftp, selected)
    ftp.quit()
    print(f"[✔] Downloaded {len(vault_bytes)} bytes")

    # Decrypt
    print(f"\n[*] Decrypting {selected} …")
    try:
        plaintext, original_name = _decrypt_vault(vault_bytes, PRIV_KEY_PATH)
    except ValueError as exc:
        print(f"[✘] Decryption failed (authentication error): {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"[✘] Decryption error: {exc}")
        sys.exit(1)

    # Save output — use original filename embedded in vault
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    out_path = Path(OUTPUT_DIR) / original_name
    out_path.write_bytes(plaintext)

    print(f"\n[✔] File decrypted and saved as original name:")
    print(f"    {out_path}")
    print(f"    Size: {len(plaintext)} bytes")
    print("\n" + "═" * 52)
    print("   Secure transfer complete. ✔")
    print("═" * 52)

    # ── Detect file type for friendly messaging ───────────────
    import subprocess
    ext = out_path.suffix.lower()
    FILE_TYPE_LABELS = {
        ".pdf"  : "PDF document",
        ".png"  : "PNG image",
        ".jpg"  : "JPEG image",
        ".jpeg" : "JPEG image",
        ".gif"  : "GIF image",
        ".webp" : "WebP image",
        ".mp4"  : "MP4 video",
        ".mkv"  : "MKV video",
        ".mp3"  : "MP3 audio",
        ".wav"  : "WAV audio",
        ".txt"  : "text file",
        ".docx" : "Word document",
        ".xlsx" : "Excel spreadsheet",
        ".pptx" : "PowerPoint presentation",
        ".zip"  : "ZIP archive",
        ".apk"  : "Android APK",
    }
    file_label = FILE_TYPE_LABELS.get(ext, f"{ext.lstrip('.').upper()} file" if ext else "file")

    # ── Open prompt ───────────────────────────────────────────
    try:
        answer = input("\n    Open file now? [Y/N]: ").strip().lower()
        if answer == "y":
            print(f"    Opening {file_label}: {out_path.name} …")
            result = subprocess.run(
                ["termux-open", str(out_path)],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"    [!] termux-open failed.")
                print(f"    Open manually: Files → Downloads → aegis_out → {out_path.name}")
            else:
                print(f"    {file_label.capitalize()} opened successfully. ✔")
        else:
            print(f"\n    {file_label.capitalize()} saved. Open it anytime:")
            print(f"    Files app → Downloads → aegis_out → {out_path.name}")
    except KeyboardInterrupt:
        print("\n    Skipped.")
    print()


if __name__ == "__main__":
    main()