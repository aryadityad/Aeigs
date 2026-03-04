"""
╔══════════════════════════════════════════════════════════════╗
║         AEGIS-HOTSPOT VAULT — Localized FTP Server           ║
║         Author : Aryaditya Deshmukh (23BCE5056)              ║
║         Institute: VIT Chennai                               ║
╚══════════════════════════════════════════════════════════════╝

Binds to 0.0.0.0:2121 and serves ./shared_vault.
The mobile Termux client (client.py) connects to 192.168.137.1:2121.

Usage:
    python server.py
"""

import os
import sys
import logging
from pathlib import Path

from pyftpdlib.handlers  import FTPHandler
from pyftpdlib.servers   import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer

# ── Config ─────────────────────────────────────────────────────
HOST          = "0.0.0.0"
PORT          = 2121
VAULT_DIR     = "./shared_vault"
FTP_USER      = "aryaditya"
FTP_PASS      = "5056"
MAX_CONS      = 10
MAX_CONS_IP   = 5
PASSIVE_PORTS = range(60000, 60100)   # for NAT traversal if needed

BANNER = (
    "Aegis Hotspot Vault FTP — Secure Bubble Active\r\n"
    "Authorized connections only. All sessions logged."
)

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt = "%H:%M:%S",
)
log = logging.getLogger("aegis.ftp")


# ── Audit Handler ──────────────────────────────────────────────
class AuditHandler(FTPHandler):
    """FTPHandler subclass with extra security logging."""

    def on_connect(self):
        log.info("CONNECT  %s:%s", self.remote_ip, self.remote_port)

    def on_disconnect(self):
        log.info("DISCONNECT  %s", self.remote_ip)

    def on_login(self, username):
        log.info("LOGIN    user=%s  from=%s", username, self.remote_ip)

    def on_login_failed(self, username, password):
        log.warning("LOGIN FAILED  user=%s  from=%s  ⚠", username, self.remote_ip)

    def on_file_sent(self, file):
        log.info("SENT     %s  → %s", file, self.remote_ip)

    def on_file_received(self, file):
        log.info("RECEIVED %s  ← %s", file, self.remote_ip)

    def on_logout(self, username):
        log.info("LOGOUT   user=%s", username)


# ── Server Bootstrap ───────────────────────────────────────────
def start_server():
    # Ensure vault directory exists
    vault_path = Path(VAULT_DIR)
    vault_path.mkdir(parents=True, exist_ok=True)
    log.info("Serving directory : %s  (%s)", vault_path.resolve(), vault_path)

    # Authorizer — single user, read-only from mobile side
    authorizer = DummyAuthorizer()
    authorizer.add_user(
        FTP_USER, FTP_PASS,
        homedir   = str(vault_path.resolve()),
        perm      = "elradfmwMT",   # full perms (laptop-side admin)
    )

    # Handler
    handler                = AuditHandler
    handler.authorizer     = authorizer
    handler.banner         = BANNER
    handler.passive_ports  = PASSIVE_PORTS
    handler.use_sendfile   = False       # compatibility

    # Server
    server = FTPServer((HOST, PORT), handler)
    server.max_cons        = MAX_CONS
    server.max_cons_per_ip = MAX_CONS_IP

    log.info("═" * 60)
    log.info("  AEGIS FTP SERVER READY")
    log.info("  Bind     : %s:%d", HOST, PORT)
    log.info("  User     : %s", FTP_USER)
    log.info("  Gateway  : 192.168.137.1:%d  (hotspot IP)", PORT)
    log.info("  Vault    : %s", vault_path.resolve())
    log.info("═" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Server shutting down …")
        server.close_all()


if __name__ == "__main__":
    start_server()
