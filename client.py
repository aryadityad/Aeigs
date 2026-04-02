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
"""

import os
import sys
import time
import socket
import ftplib
import subprocess
import concurrent.futures
from pathlib import Path

from Crypto.PublicKey import RSA
from Crypto.Cipher    import AES, PKCS1_OAEP

# ── Config ─────────────────────────────────────────────────────
# SERVER_IP is auto-detected by scanning the subnet.
# Set to a specific IP to skip scanning (faster if IP is known).
SERVER_IP     = None               # None = auto-scan
SERVER_PORT   = 2121
FTP_USER      = "aryaditya"
FTP_PASS      = "5056"
PRIV_KEY_PATH = os.path.expanduser("~/private.pem")
OUTPUT_DIR    = os.path.expanduser("~/storage/downloads/aegis_out")

# Subnets to scan when SERVER_IP is None
SCAN_SUBNETS  = ["192.168.137", "192.168.1", "192.168.0", "10.0.0"]
SCAN_TIMEOUT  = 0.4   # seconds per host
SCAN_WORKERS  = 60    # parallel threads

# Vault format constants
VAULT_MAGIC    = b"AEGISVLT"
RSA_BLOCK_SIZE = 256
NONCE_SIZE     = 16
TAG_SIZE       = 16

# ── ANSI colour helpers ────────────────────────────────────────
def _c(code: str, text: str) -> str:
    """Wrap text in an ANSI colour code."""
    CODES = {
        "cyan"   : "\033[96m",
        "green"  : "\033[92m",
        "yellow" : "\033[93m",
        "red"    : "\033[91m",
        "blue"   : "\033[94m",
        "magenta": "\033[95m",
        "white"  : "\033[97m",
        "dim"    : "\033[2m",
        "bold"   : "\033[1m",
        "reset"  : "\033[0m",
    }
    return f"{CODES.get(code, '')}{text}\033[0m"

def _box(lines: list, color: str = "cyan", width: int = 54) -> str:
    """Render a box around a list of strings."""
    top    = _c(color, "╔" + "═" * width + "╗")
    bottom = _c(color, "╚" + "═" * width + "╝")
    rows   = []
    for line in lines:
        # strip existing ANSI for length measurement
        import re
        clean = re.sub(r'\033\[[0-9;]*m', '', line)
        pad   = width - len(clean) - 2
        rows.append(_c(color, "║") + " " + line + " " * max(pad, 0) + _c(color, "║"))
    return "\n".join([top] + rows + [bottom])

def _fmt_bytes(n: int) -> str:
    if n >= 1_048_576: return f"{n/1_048_576:.2f} MB"
    if n >= 1024:      return f"{n/1024:.1f} KB"
    return f"{n} B"

def _fmt_speed(bps: float) -> str:
    if bps >= 1_048_576: return f"{bps/1_048_576:.2f} MB/s"
    if bps >= 1024:      return f"{bps/1024:.1f} KB/s"
    return f"{bps:.0f} B/s"

def _fmt_eta(secs: float) -> str:
    if secs < 0 or secs > 3600: return "--:--"
    m, s = divmod(int(secs), 60)
    return f"{m:02d}:{s:02d}"


# ── Animated banner ────────────────────────────────────────────
def _banner():
    os.system("clear")
    lines = [
        "",
        _c("cyan",  "bold") + "  ╔═══════════════════════════════════════════════════╗",
        _c("cyan",  "")     + "  ║" + _c("bold", _c("white", "    🛡️  AEGIS HOTSPOT VAULT — SECURE CLIENT    ")) + _c("cyan", "║"),
        _c("cyan",  "")     + "  ║" + _c("dim",  "       Aryaditya Deshmukh · 23BCE5056 · VIT       ") + _c("cyan", "║"),
        _c("cyan",  "")     + "  ╚═══════════════════════════════════════════════════╝",
        "",
    ]
    print("\n".join(lines))


# ── Status line helpers ────────────────────────────────────────
def _status(icon: str, msg: str, color: str = "white"):
    print(f"  {icon}  {_c(color, msg)}")

def _ok(msg: str):      _status(_c("green",  "✔"), msg, "green")
def _info(msg: str):    _status(_c("cyan",   "◆"), msg, "white")
def _warn(msg: str):    _status(_c("yellow", "⚠"), msg, "yellow")
def _err(msg: str):     _status(_c("red",    "✘"), msg, "red")
def _step(n: int, total: int, msg: str):
    tag = _c("magenta", f"[{n}/{total}]")
    print(f"\n  {tag}  {_c('bold', msg)}")


# ── Live progress bar with speed + ETA ────────────────────────
def _live_progress(transferred: int, total: int,
                   start_time: float, bar_width: int = 36):
    elapsed = time.time() - start_time or 0.001
    speed   = transferred / elapsed
    pct     = transferred / total if total else 0
    filled  = int(bar_width * pct)
    eta     = (total - transferred) / speed if speed > 0 and total else 0

    bar     = _c("green",  "█" * filled) + _c("dim", "░" * (bar_width - filled))
    pct_str = _c("bold",   f"{pct*100:5.1f}%")
    spd_str = _c("yellow", _fmt_speed(speed))
    eta_str = _c("cyan",   f"ETA {_fmt_eta(eta)}")
    sz_str  = _c("dim",    f"{_fmt_bytes(transferred)} / {_fmt_bytes(total)}")

    line = f"\r  [{bar}] {pct_str}  {spd_str}  {eta_str}  {sz_str}   "
    sys.stdout.write(line)
    sys.stdout.flush()
    if transferred >= total:
        print()


# ── Crypto stage animator ──────────────────────────────────────
CRYPTO_STAGES = [
    ("RSA-OAEP",  "Unwrapping AES session key with private key"),
    ("AES-GCM",   "Decrypting ciphertext"),
    ("AUTH TAG",  "Verifying 128-bit authentication tag"),
    ("ASSEMBLE",  "Writing decrypted file to storage"),
]

def _animate_stage(idx: int, label: str, detail: str, done: bool = False):
    icon  = _c("green", "✔") if done else _c("yellow", "⟳")
    tag   = _c("cyan" if not done else "green", f"[{label:<10}]")
    print(f"  {icon}  {tag}  {_c('dim', detail)}")


# ── Vault decryption ───────────────────────────────────────────
def _decrypt_vault(vault_bytes: bytes, priv_key_path: str):
    magic = vault_bytes[:8]
    if magic != VAULT_MAGIC:
        raise ValueError("Not a valid Aegis vault (bad magic bytes).")

    offset        = 9
    fname_len     = int.from_bytes(vault_bytes[offset:offset+2], "big"); offset += 2
    original_name = vault_bytes[offset:offset+fname_len].decode("utf-8"); offset += fname_len
    wrapped_key   = vault_bytes[offset : offset + RSA_BLOCK_SIZE]; offset += RSA_BLOCK_SIZE
    nonce         = vault_bytes[offset : offset + NONCE_SIZE];     offset += NONCE_SIZE
    tag           = vault_bytes[offset : offset + TAG_SIZE];       offset += TAG_SIZE
    ciphertext    = vault_bytes[offset:]

    print()
    for i, (label, detail) in enumerate(CRYPTO_STAGES):
        _animate_stage(i + 1, label, detail, done=False)

    # Slight delay so each stage is visible during demo
    time.sleep(0.3)

    # RSA unwrap
    priv_key   = RSA.import_key(Path(priv_key_path).read_bytes())
    cipher_rsa = PKCS1_OAEP.new(priv_key)
    aes_key    = cipher_rsa.decrypt(wrapped_key)

    time.sleep(0.2)

    # AES-GCM decrypt
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce, mac_len=TAG_SIZE)
    plaintext  = cipher_aes.decrypt_and_verify(ciphertext, tag)

    # Redraw stages as done
    print(f"\033[{len(CRYPTO_STAGES)}A", end="")   # move cursor up
    for i, (label, detail) in enumerate(CRYPTO_STAGES):
        _animate_stage(i + 1, label, detail, done=True)

    return plaintext, original_name, aes_key, nonce, tag


# ── FTP helpers ────────────────────────────────────────────────
def _list_vaults(ftp: ftplib.FTP) -> list:
    return [f for f in ftp.nlst() if f.endswith(".vault")]


def _download_vault(ftp: ftplib.FTP, filename: str) -> bytes:
    try:    total = ftp.size(filename)
    except: total = 0

    chunks      = []
    transferred = 0
    start       = time.time()

    def _collect(chunk: bytes):
        nonlocal transferred
        chunks.append(chunk)
        transferred += len(chunk)
        _live_progress(transferred, total, start)

    ftp.retrbinary(f"RETR {filename}", _collect, blocksize=8192)
    elapsed = time.time() - start or 0.001
    return b"".join(chunks), elapsed


# ── File type labels ───────────────────────────────────────────
FILE_LABELS = {
    ".pdf": "PDF document", ".png": "PNG image",
    ".jpg": "JPEG image",   ".jpeg": "JPEG image",
    ".gif": "GIF image",    ".webp": "WebP image",
    ".mp4": "MP4 video",    ".mkv": "MKV video",
    ".mp3": "MP3 audio",    ".wav": "WAV audio",
    ".txt": "text file",    ".docx": "Word document",
    ".xlsx": "Excel spreadsheet", ".pptx": "PowerPoint",
    ".zip": "ZIP archive",  ".apk": "Android APK",
}


# ── Main ───────────────────────────────────────────────────────
def main():
    _banner()

    # ── Check private key ──────────────────────────────────────
    _step(1, 5, "Checking credentials")
    if not Path(PRIV_KEY_PATH).exists():
        _err(f"Private key not found: {PRIV_KEY_PATH}")
        _warn("Copy private.pem to your phone first.")
        sys.exit(1)
    _ok(f"Private key found  →  {PRIV_KEY_PATH}")

    # ── Auto-detect or use configured server IP ───────────────
    target_ip = SERVER_IP
    _step(2, 5, "Locating Aegis server" if target_ip is None else f"Connecting to {target_ip}:{SERVER_PORT}")

    if target_ip is None:
        _info(f"No IP configured — scanning {len(SCAN_SUBNETS)} subnet(s) for Aegis FTP server…")
        print()
        target_ip = _auto_detect_server(SERVER_PORT)
        if target_ip is None:
            _err("No Aegis server found on any subnet.")
            _warn("Make sure the laptop hotspot is ON and server.py is running.")
            _info(f"Or set SERVER_IP manually at the top of this file.")
            sys.exit(1)
        _ok(f"Server found  →  {_c('cyan', target_ip)}:{SERVER_PORT}")

    # ── FTP connect ────────────────────────────────────────────
    try:
        ftp = ftplib.FTP()
        ftp.connect(target_ip, SERVER_PORT, timeout=10)
        ftp.login(FTP_USER, FTP_PASS)
        _ok(f"Connected  ·  user={FTP_USER}  ·  {target_ip}:{SERVER_PORT}")
    except Exception as exc:
        _err(f"FTP connection failed: {exc}")
        sys.exit(1)

    # ── List vaults ────────────────────────────────────────────
    _step(3, 5, "Scanning vault directory")
    vaults = _list_vaults(ftp)
    if not vaults:
        _warn("No .vault files found on server.")
        _info("Encrypt a file on the laptop first, then retry.")
        ftp.quit()
        sys.exit(0)

    print()
    print(_c("dim", "  " + "─" * 50))
    print(f"  {_c('bold', 'Available Vaults')}   {_c('dim', f'({len(vaults)} found)')}")
    print(_c("dim", "  " + "─" * 50))
    for i, v in enumerate(vaults):
        try:    sz = _fmt_bytes(ftp.size(v))
        except: sz = "?"
        print(f"  {_c('cyan', f'[{i}]')}  {_c('white', v):<40} {_c('dim', sz)}")
    print(_c("dim", "  " + "─" * 50))

    if len(vaults) == 1:
        choice = 0
        print(f"\n  {_c('dim', 'Auto-selected:')}  {_c('green', vaults[0])}")
    else:
        try:
            raw    = input(f"\n  {_c('yellow', '▶')}  Select vault index: ")
            choice = int(raw.strip())
        except (ValueError, KeyboardInterrupt):
            print()
            _warn("Aborted.")
            ftp.quit()
            sys.exit(0)

    if choice not in range(len(vaults)):
        _err("Invalid selection.")
        ftp.quit()
        sys.exit(1)

    selected = vaults[choice]

    # ── Download ───────────────────────────────────────────────
    _step(4, 5, f"Downloading  →  {selected}")
    print()
    vault_bytes, elapsed = _download_vault(ftp, selected)
    ftp.quit()

    total_bytes = len(vault_bytes)
    avg_speed   = total_bytes / elapsed if elapsed else 0
    print()
    _ok(f"Download complete  ·  {_fmt_bytes(total_bytes)}  ·  avg {_fmt_speed(avg_speed)}  ·  {elapsed:.2f}s")

    # ── Decrypt ────────────────────────────────────────────────
    _step(5, 5, "Decrypting vault")
    try:
        plaintext, original_name, aes_key, nonce, tag = \
            _decrypt_vault(vault_bytes, PRIV_KEY_PATH)
    except ValueError as exc:
        print()
        _err(f"Authentication failed — vault may be tampered: {exc}")
        sys.exit(1)
    except Exception as exc:
        print()
        _err(f"Decryption error: {exc}")
        sys.exit(1)

    # ── Save file ──────────────────────────────────────────────
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    out_path = Path(OUTPUT_DIR) / original_name
    out_path.write_bytes(plaintext)

    ext        = out_path.suffix.lower()
    file_label = FILE_LABELS.get(ext, f"{ext.lstrip('.').upper()} file" if ext else "file")

    # ── Summary box ────────────────────────────────────────────
    print()
    print(_c("dim", "  " + "─" * 50))
    print(f"  {_c('bold', _c('green', '✔  SECURE TRANSFER COMPLETE'))}")
    print(_c("dim", "  " + "─" * 50))
    print(f"  {'File':<18}  {_c('white',  original_name)}")
    print(f"  {'Type':<18}  {_c('cyan',   file_label)}")
    print(f"  {'Size':<18}  {_c('yellow', _fmt_bytes(len(plaintext)))}")
    print(f"  {'Transfer speed':<18}  {_c('yellow', _fmt_speed(avg_speed))}")
    print(f"  {'Transfer time':<18}  {_c('dim',    f'{elapsed:.2f}s')}")
    print(f"  {'AES key (hex)':<18}  {_c('dim',    aes_key.hex()[:24] + '…')}")
    print(f"  {'GCM nonce':<18}  {_c('dim',    nonce.hex()[:24] + '…')}")
    print(f"  {'Auth tag':<18}  {_c('dim',    tag.hex())}")
    print(f"  {'Saved to':<18}  {_c('dim',    str(out_path))}")
    print(_c("dim", "  " + "─" * 50))

    # ── Open prompt ────────────────────────────────────────────
    try:
        prompt = f"\n  {_c('yellow', '▶')}  Open {file_label} now? {_c('dim', '[Y/N]')}: "
        answer = input(prompt).strip().lower()
        print()
        if answer == "y":
            _info(f"Launching {file_label}: {out_path.name} …")
            result = subprocess.run(
                ["termux-open", str(out_path)],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                _warn("termux-open failed. Open manually:")
                _info(f"Files → Downloads → aegis_out → {out_path.name}")
            else:
                _ok(f"{file_label.capitalize()} opened successfully.")
        else:
            _info(f"{file_label.capitalize()} saved. Open anytime:")
            _info(f"Files → Downloads → aegis_out → {out_path.name}")
    except KeyboardInterrupt:
        print()
        _warn("Skipped.")

    print()


if __name__ == "__main__":
    main()