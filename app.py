"""
╔══════════════════════════════════════════════════════════════╗
║         AEGIS-HOTSPOT VAULT — Streamlit Dashboard            ║
║         Author : Aryaditya Deshmukh (23BCE5056)              ║
║         Institute: VIT Chennai                               ║
╚══════════════════════════════════════════════════════════════╝

Run:
    streamlit run app.py
"""

import time
import tempfile
import os
from pathlib import Path

import streamlit as st
from crypto_core import generate_rsa_keypair, encrypt_file

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Aegis Hotspot Vault",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark sleek CSS ─────────────────────────────────────────────
st.markdown("""
<style>
  /* Base */
  html, body, [class*="css"] {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
  }
  .stApp { background: #0d0f14; color: #c9d1d9; }

  /* Sidebar */
  section[data-testid="stSidebar"] { background: #0a0c10 !important; }

  /* Glowing title */
  .aegis-title {
    font-size: 2.2rem; font-weight: 800; letter-spacing: 0.08em;
    background: linear-gradient(135deg, #58a6ff, #3fb950, #58a6ff);
    background-size: 200%;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: shimmer 4s linear infinite;
  }
  @keyframes shimmer { 0%{background-position:0%} 100%{background-position:200%} }

  /* Stage card */
  .stage-card {
    border: 1px solid #30363d; border-radius: 10px;
    padding: 16px 20px; margin: 6px 0;
    transition: all 0.3s ease;
  }
  .stage-pending  { background: #161b22; border-color: #30363d; color: #6e7681; }
  .stage-active   { background: #1c2333; border-color: #58a6ff;
                    box-shadow: 0 0 18px rgba(88,166,255,0.35); color: #58a6ff; }
  .stage-done     { background: #0d1117; border-color: #3fb950;
                    box-shadow: 0 0 12px rgba(63,185,80,0.25);  color: #3fb950; }

  /* Terminal log box */
  .log-box {
    background: #010409; border: 1px solid #21262d;
    border-radius: 8px; padding: 14px;
    font-family: 'Courier New', monospace; font-size: 0.78rem;
    color: #39d353; max-height: 320px; overflow-y: auto;
    white-space: pre-wrap; word-break: break-all;
  }

  /* Metric cards */
  div[data-testid="metric-container"] {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 8px; padding: 10px;
  }

  /* Buttons */
  .stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: #fff; border: none; border-radius: 6px;
    font-weight: 700; letter-spacing: 0.05em;
    padding: 0.5rem 1.8rem;
    transition: all 0.2s;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #2ea043, #3fb950);
    box-shadow: 0 0 14px rgba(63,185,80,0.5);
    transform: translateY(-1px);
  }

  /* File uploader */
  [data-testid="stFileUploader"] {
    background: #161b22; border: 2px dashed #30363d;
    border-radius: 10px; padding: 10px;
  }
  [data-testid="stFileUploader"]:hover { border-color: #58a6ff; }

  hr { border-color: #21262d; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️  Configuration")
    st.markdown("---")

    vault_dir = st.text_input("Vault Output Directory", value="./shared_vault")
    pub_key_path = st.text_input("RSA Public Key Path", value="public.pem")

    st.markdown("---")
    st.markdown("**🔑 Key Management**")

    if st.button("Generate New RSA-2048 Keypair"):
        with st.spinner("Generating 2048-bit RSA keypair…"):
            try:
                pub, priv = generate_rsa_keypair(".")
                st.success(f"✔ Keys generated")
                st.code(f"Public : {pub}\nPrivate: {priv} ⚠ KEEP SECRET", language="bash")
            except Exception as exc:
                st.error(f"Key generation failed: {exc}")

    st.markdown("---")
    st.markdown("**ℹ️ About**")
    st.markdown(
        "**Aegis Hotspot Vault**  \n"
        "RSA-2048 + AES-256-GCM  \n"
        "Offline-first secure bubble  \n"
        "[Aryaditya Deshmukh](https://github.com/aryadityad/)"
    )
    st.markdown("*VIT Chennai · 23BCE5056*")

# ── Header ─────────────────────────────────────────────────────
st.markdown('<p class="aegis-title">🛡️ AEGIS HOTSPOT VAULT</p>', unsafe_allow_html=True)
st.markdown("**RSA-2048 · AES-256-GCM · Offline Secure Bubble**")
st.markdown("---")

# ── Pipeline Stage Renderer ────────────────────────────────────
STAGES = [
    ("🔑", "KEY_GEN",        "AES-256 Session Key Generation"),
    ("🔐", "RSA_WRAP",       "RSA-2048 OAEP Key Wrapping"),
    ("🔒", "AES_ENCRYPT",    "AES-256-GCM File Encryption"),
    ("📦", "VAULT_ASSEMBLY", "Vault Assembly & Write"),
]

def render_pipeline(active_stage: str | None = None, done_stages: list = []):
    cols = st.columns(len(STAGES))
    for i, (icon, key, label) in enumerate(STAGES):
        if key in done_stages:
            cls = "stage-done";    symbol = "✔"
        elif key == active_stage:
            cls = "stage-active";  symbol = "⟳"
        else:
            cls = "stage-pending"; symbol = "○"
        cols[i].markdown(
            f'<div class="stage-card {cls}">'
            f'<b>{icon} {symbol}</b><br><small>{label}</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Upload section ─────────────────────────────────────────────
col1, col2 = st.columns([1.4, 1])

with col1:
    st.markdown("### 📁 Drop File to Vault")
    uploaded = st.file_uploader(
        "Drag & drop any file", label_visibility="collapsed"
    )

    st.markdown("### 🔬 Encryption Pipeline")
    pipeline_placeholder = st.empty()

    # Initial idle render
    with pipeline_placeholder.container():
        render_pipeline()

    log_placeholder = st.empty()

with col2:
    st.markdown("### 📊 Vault Metrics")
    m1, m2 = st.columns(2)
    m3, m4 = st.columns(2)
    metric_plaintext  = m1.empty()
    metric_ciphertext = m2.empty()
    metric_overhead   = m3.empty()
    metric_vault_size = m4.empty()

    metric_plaintext.metric("Plaintext",  "—")
    metric_ciphertext.metric("Ciphertext","—")
    metric_overhead.metric("Overhead",   "—")
    metric_vault_size.metric("Vault Size","—")

    st.markdown("### 🖥️ Live Hex Inspector")
    hex_placeholder = st.empty()
    hex_placeholder.markdown(
        '<div class="log-box">// Waiting for encryption run…</div>',
        unsafe_allow_html=True,
    )

# ── Run Button ─────────────────────────────────────────────────
run_col, _ = st.columns([1, 3])
run_btn = run_col.button("🚀  Vault It!", use_container_width=True)

# ── Encryption Run ─────────────────────────────────────────────
if run_btn:
    if uploaded is None:
        st.warning("⚠️  Please upload a file first.")
        st.stop()

    if not Path(pub_key_path).exists():
        st.error("❌  RSA public key not found. Generate keys first (sidebar).")
        st.stop()

    # Save upload to temp
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(uploaded.name).suffix
    ) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    logs  = []
    done  = []
    state = {"active": None}   # mutable container — avoids nonlocal binding issue

    def push_log(msg: str):
        logs.append(msg)
        log_placeholder.markdown(
            f'<div class="log-box">{"<br>".join(logs)}</div>',
            unsafe_allow_html=True,
        )

    def progress(stage: str):
        if state["active"]:
            done.append(state["active"])
        state["active"] = stage
        with pipeline_placeholder.container():
            render_pipeline(active_stage=state["active"], done_stages=done)
        push_log(f"<span style='color:#58a6ff'>▶ Stage: {stage}</span>")
        time.sleep(0.4)   # visual pause so stages are visible

    try:
        with st.spinner("Encrypting…"):
            vault_path, meta = encrypt_file(
                plaintext_path  = tmp_path,
                public_key_path = pub_key_path,
                output_dir      = vault_dir,
                progress_cb     = progress,
            )

        # Final pipeline render — all done
        if state["active"]:
            done.append(state["active"])
        with pipeline_placeholder.container():
            render_pipeline(active_stage=None, done_stages=done)

        push_log("<span style='color:#3fb950'>✔ Vault sealed successfully!</span>")

        # ── Metrics ──────────────────────────────────────────
        plain_sz  = meta["plaintext_size"]
        cipher_sz = meta["ciphertext_size"]
        vault_sz  = Path(vault_path).stat().st_size
        overhead  = vault_sz - plain_sz

        def _fmt(n):
            return f"{n/1024:.1f} KB" if n >= 1024 else f"{n} B"

        metric_plaintext.metric("Plaintext",   _fmt(plain_sz))
        metric_ciphertext.metric("Ciphertext", _fmt(cipher_sz))
        metric_overhead.metric("Overhead",     _fmt(overhead))
        metric_vault_size.metric("Vault Size",  _fmt(vault_sz))

        # ── Hex Inspector ─────────────────────────────────────
        hex_lines = [
            f"<b style='color:#58a6ff'>// AEGIS VAULT INSPECTOR</b>",
            f"<b style='color:#e3b341'>File        :</b> {uploaded.name}",
            f"<b style='color:#e3b341'>Vault Path  :</b> {vault_path}",
            "",
            f"<b style='color:#58a6ff'>// AES-256-GCM Session Key (32 bytes)</b>",
            f"<span style='color:#39d353'>{meta['aes_key_hex']}</span>",
            "",
            f"<b style='color:#58a6ff'>// RSA-2048 Public Modulus (truncated)</b>",
            f"<span style='color:#d2a8ff'>{meta['rsa_pub_hex'][:96]}…</span>",
            "",
            f"<b style='color:#58a6ff'>// AES Nonce (16 bytes)</b>",
            f"<span style='color:#ffa657'>{meta['nonce_hex']}</span>",
            "",
            f"<b style='color:#58a6ff'>// GCM Auth Tag (16 bytes)</b>",
            f"<span style='color:#ff7b72'>{meta['tag_hex']}</span>",
            "",
            f"<b style='color:#3fb950'>// VAULT FILE LAYOUT</b>",
            f"  [RSA-Wrapped AES Key : 256 B]",
            f"  [Nonce               :  16 B]",
            f"  [Auth Tag            :  16 B]",
            f"  [Ciphertext          : {cipher_sz} B]",
        ]
        hex_placeholder.markdown(
            f'<div class="log-box">{"<br>".join(hex_lines)}</div>',
            unsafe_allow_html=True,
        )

        st.success(f"🛡️  Vault ready: `{vault_path}`  — serve via FTP server!")

    except Exception as exc:
        st.error(f"❌  Encryption failed: {exc}")
        push_log(f"<span style='color:#ff7b72'>ERROR: {exc}</span>")
    finally:
        os.unlink(tmp_path)