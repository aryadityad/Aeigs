"""
╔══════════════════════════════════════════════════════════════╗
║           AEGIS-HOTSPOT VAULT — Cryptographic Core           ║
║           Author : Aryaditya Deshmukh (23BCE5056)            ║
║           Institute: VIT Chennai                             ║
╚══════════════════════════════════════════════════════════════╝

Vault File Format
─────────────────
┌──────────────────┬───────────┬──────────────┬────────────────┐
│ RSA-Wrapped AES  │   Nonce   │   Auth Tag   │   Ciphertext   │
│    Key (256 B)   │  (16 B)   │   (16 B)     │   (variable)   │
└──────────────────┴───────────┴──────────────┴────────────────┘
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Callable, Optional

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes

# ── Constants ──────────────────────────────────────────────────
RSA_KEY_SIZE   = 2048          # bits
AES_KEY_SIZE   = 32            # bytes  → AES-256
NONCE_SIZE     = 16            # bytes
TAG_SIZE       = 16            # bytes
RSA_BLOCK_SIZE = 256           # bytes  (RSA-2048 output)

VAULT_MAGIC    = b"AEGISVLT"   # 8-byte magic header
VAULT_VERSION  = b"\x01"       # format version

logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("aegis.crypto")


# ── Key Generation ─────────────────────────────────────────────

def generate_rsa_keypair(key_dir: str = ".") -> Tuple[str, str]:
    """
    Generate an RSA-2048 keypair and persist to disk.

    Returns
    -------
    (public_key_path, private_key_path)
    """
    log.info("Generating RSA-2048 keypair …")
    key = RSA.generate(RSA_KEY_SIZE)

    pub_path  = Path(key_dir) / "public.pem"
    priv_path = Path(key_dir) / "private.pem"

    pub_path.write_bytes(key.publickey().export_key("PEM"))
    priv_path.write_bytes(key.export_key("PEM"))

    log.info("Public  key → %s", pub_path)
    log.info("Private key → %s  ⚠  NEVER commit this!", priv_path)
    return str(pub_path), str(priv_path)


def load_public_key(path: str) -> RSA.RsaKey:
    return RSA.import_key(Path(path).read_bytes())


def load_private_key(path: str) -> RSA.RsaKey:
    return RSA.import_key(Path(path).read_bytes())


# ── Encryption Pipeline ────────────────────────────────────────

def encrypt_file(
    plaintext_path: str,
    public_key_path: str,
    output_dir: str = "./shared_vault",
    progress_cb: Optional[Callable[[str], None]] = None,
) -> Tuple[str, dict]:
    """
    Full encrypt pipeline: plaintext → .vault file

    Parameters
    ----------
    plaintext_path  : path to the file to encrypt
    public_key_path : RSA public key (.pem)
    output_dir      : directory where the .vault is saved
    progress_cb     : optional callback(stage_name) for UI updates

    Returns
    -------
    (vault_path, metadata_dict)
    """

    def _step(stage: str):
        log.info("Stage: %s", stage)
        if progress_cb:
            progress_cb(stage)

    # ── Stage 1 : Key Generation ──────────────────────────────
    _step("KEY_GEN")
    aes_key = get_random_bytes(AES_KEY_SIZE)
    log.info("AES-256 session key  : %s…", aes_key.hex()[:32])

    # ── Stage 2 : RSA Wrap ────────────────────────────────────
    _step("RSA_WRAP")
    pub_key  = load_public_key(public_key_path)
    cipher_rsa = PKCS1_OAEP.new(pub_key)
    wrapped_key = cipher_rsa.encrypt(aes_key)          # 256 bytes
    log.info("RSA public key (mod) : %s…",
             pub_key.n.to_bytes(256, "big").hex()[:32])
    assert len(wrapped_key) == RSA_BLOCK_SIZE, "RSA block size mismatch"

    # ── Stage 3 : AES-256-GCM Encryption ─────────────────────
    _step("AES_ENCRYPT")
    nonce      = get_random_bytes(NONCE_SIZE)
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce, mac_len=TAG_SIZE)
    plaintext  = Path(plaintext_path).read_bytes()
    ciphertext, tag = cipher_aes.encrypt_and_digest(plaintext)
    log.info("Nonce                : %s", nonce.hex())
    log.info("Auth Tag             : %s", tag.hex())
    log.info("Ciphertext size      : %d bytes", len(ciphertext))

    # ── Stage 4 : Vault Assembly ──────────────────────────────
    _step("VAULT_ASSEMBLY")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem       = Path(plaintext_path).stem
    vault_path = Path(output_dir) / f"{stem}.vault"

    # Encode original filename so client can restore extension
    orig_name       = Path(plaintext_path).name.encode("utf-8")  # e.g. b"report.pdf"
    orig_name_len   = len(orig_name).to_bytes(2, "big")          # 2-byte length prefix

    with open(vault_path, "wb") as f:
        f.write(VAULT_MAGIC)          # magic       8 B
        f.write(VAULT_VERSION)        # version     1 B
        f.write(orig_name_len)        # filename len 2 B
        f.write(orig_name)            # filename    variable
        f.write(wrapped_key)          # RSA key     256 B
        f.write(nonce)                # nonce       16 B
        f.write(tag)                  # auth tag    16 B
        f.write(ciphertext)           # ciphertext  variable

    log.info("Vault written        : %s  (%d bytes total)",
             vault_path, vault_path.stat().st_size)

    metadata = {
        "aes_key_hex"     : aes_key.hex(),
        "rsa_pub_hex"     : pub_key.n.to_bytes(256, "big").hex(),
        "nonce_hex"       : nonce.hex(),
        "tag_hex"         : tag.hex(),
        "vault_path"      : str(vault_path),
        "plaintext_size"  : len(plaintext),
        "ciphertext_size" : len(ciphertext),
    }
    return str(vault_path), metadata


# ── Decryption Pipeline ────────────────────────────────────────

def decrypt_vault(vault_path: str, private_key_path: str,
                  output_dir: str = ".") -> str:
    """
    Decrypt a .vault file back to plaintext.

    Returns
    -------
    Path to the recovered plaintext file.
    """
    log.info("Opening vault : %s", vault_path)
    data = Path(vault_path).read_bytes()

    # Parse magic + version
    magic   = data[:8]
    version = data[8:9]
    if magic != VAULT_MAGIC:
        raise ValueError("Not a valid Aegis vault file (bad magic).")
    log.info("Magic OK  version=%s", version.hex())

    offset      = 9
    wrapped_key = data[offset : offset + RSA_BLOCK_SIZE]; offset += RSA_BLOCK_SIZE
    nonce       = data[offset : offset + NONCE_SIZE];     offset += NONCE_SIZE
    tag         = data[offset : offset + TAG_SIZE];       offset += TAG_SIZE
    ciphertext  = data[offset:]

    # RSA unwrap
    priv_key   = load_private_key(private_key_path)
    cipher_rsa = PKCS1_OAEP.new(priv_key)
    aes_key    = cipher_rsa.decrypt(wrapped_key)
    log.info("AES key recovered    : %s…", aes_key.hex()[:32])

    # AES-GCM decrypt + verify
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce, mac_len=TAG_SIZE)
    plaintext  = cipher_aes.decrypt_and_verify(ciphertext, tag)
    log.info("Auth tag verified ✔")

    # Write output
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem     = Path(vault_path).stem
    out_path = Path(output_dir) / f"{stem}.dec"
    out_path.write_bytes(plaintext)
    log.info("Decrypted file       : %s", out_path)
    return str(out_path)


# ── CLI ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse, sys

    parser = argparse.ArgumentParser(description="Aegis Crypto Core CLI")
    sub    = parser.add_subparsers(dest="cmd")

    g = sub.add_parser("genkeys", help="Generate RSA-2048 keypair")
    g.add_argument("--dir", default=".", help="Output directory")

    e = sub.add_parser("encrypt", help="Encrypt a file")
    e.add_argument("file")
    e.add_argument("--pub",    default="public.pem")
    e.add_argument("--outdir", default="./shared_vault")

    d = sub.add_parser("decrypt", help="Decrypt a .vault file")
    d.add_argument("vault")
    d.add_argument("--priv",   default="private.pem")
    d.add_argument("--outdir", default=".")

    args = parser.parse_args()

    if args.cmd == "genkeys":
        generate_rsa_keypair(args.dir)
    elif args.cmd == "encrypt":
        vault, meta = encrypt_file(args.file, args.pub, args.outdir)
        print(f"\n✔  Vault created: {vault}")
    elif args.cmd == "decrypt":
        out = decrypt_vault(args.vault, args.priv, args.outdir)
        print(f"\n✔  Decrypted: {out}")
    else:
        parser.print_help()
        sys.exit(1)