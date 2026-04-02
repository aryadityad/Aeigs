"""
╔══════════════════════════════════════════════════════════════╗
║         AEGIS-HOTSPOT VAULT — Streamlit Dashboard            ║
║         Author : Aryaditya Deshmukh (23BCE5056)              ║
║         Institute: VIT Chennai                               ║
╚══════════════════════════════════════════════════════════════╝

Run:
    python -m streamlit run app.py
"""

import time
import tempfile
import os
from pathlib import Path

import io
import base64
import streamlit as st
from crypto_core import generate_rsa_keypair, encrypt_file

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title = "Aegis Hotspot Vault",
    page_icon  = "🛡️",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
  }
  .stApp { background: #0d0f14; color: #c9d1d9; }
  section[data-testid="stSidebar"] { background: #080a0e !important; }

  /* ── Title ── */
  .aegis-title {
    font-size: 2.4rem; font-weight: 800; letter-spacing: 0.1em;
    background: linear-gradient(135deg, #58a6ff 0%, #3fb950 50%, #58a6ff 100%);
    background-size: 200%;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: shimmer 5s linear infinite;
    margin: 0; padding: 0;
  }
  .aegis-sub {
    color: #6e7681; font-size: 0.85rem; letter-spacing: 0.15em;
    margin-top: 4px;
  }
  @keyframes shimmer { 0%{background-position:0%} 100%{background-position:200%} }

  /* ── GitHub badge ── */
  .gh-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: #161b22; border: 1px solid #30363d;
    border-radius: 20px; padding: 6px 14px;
    text-decoration: none; color: #c9d1d9;
    font-size: 0.8rem; transition: all 0.2s;
  }
  .gh-badge:hover {
    border-color: #58a6ff;
    box-shadow: 0 0 12px rgba(88,166,255,0.3);
    color: #58a6ff;
  }
  .gh-badge svg { fill: #c9d1d9; }

  /* ── Section headers ── */
  .section-header {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.2em;
    color: #58a6ff; text-transform: uppercase;
    border-bottom: 1px solid #21262d; padding-bottom: 6px;
    margin: 24px 0 14px 0;
  }

  /* ── How it works cards ── */
  .how-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    margin: 12px 0;
  }
  .how-card {
    background: #0d1117; border: 1px solid #21262d;
    border-radius: 10px; padding: 16px 14px;
    position: relative; overflow: hidden;
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  .how-card:hover {
    border-color: #30363d;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
  }
  .how-card::before {
    content: attr(data-step);
    position: absolute; top: 10px; right: 12px;
    font-size: 1.8rem; font-weight: 900; color: #161b22;
  }
  .how-icon  { font-size: 1.5rem; margin-bottom: 8px; }
  .how-title { font-size: 0.75rem; font-weight: 700; color: #e6edf3; margin-bottom: 4px; }
  .how-desc  { font-size: 0.7rem; color: #8b949e; line-height: 1.5; }
  .how-tag   {
    display: inline-block; margin-top: 8px;
    background: #161b22; border: 1px solid #30363d;
    border-radius: 4px; padding: 2px 7px;
    font-size: 0.65rem; color: #58a6ff;
  }

  /* ── Explainer blocks ── */
  .explainer {
    background: #0d1117; border-left: 3px solid #58a6ff;
    border-radius: 0 8px 8px 0; padding: 14px 18px;
    margin: 10px 0; font-size: 0.8rem; line-height: 1.7;
    color: #8b949e;
  }
  .explainer b { color: #e6edf3; }
  .explainer code {
    background: #161b22; padding: 1px 6px;
    border-radius: 4px; color: #79c0ff; font-size: 0.75rem;
  }

  /* ── Vault format table ── */
  .vault-format {
    background: #010409; border: 1px solid #21262d;
    border-radius: 8px; padding: 14px;
    font-size: 0.72rem; color: #39d353;
    font-family: 'Courier New', monospace;
    overflow-x: auto; white-space: pre;
  }

  /* ── Flow arrow ── */
  .flow-arrow {
    display: flex; align-items: center; gap: 8px;
    margin: 6px 0; font-size: 0.78rem;
  }
  .flow-dot {
    width: 8px; height: 8px; border-radius: 50%;
    flex-shrink: 0;
  }

  /* ── Pipeline stage cards ── */
  .stage-card {
    border: 1px solid #30363d; border-radius: 10px;
    padding: 14px 16px; margin: 4px 0;
    transition: all 0.3s ease; text-align: center;
  }
  .stage-pending  { background: #0d1117; border-color: #21262d; color: #484f58; }
  .stage-active   {
    background: #1c2333; border-color: #58a6ff;
    box-shadow: 0 0 20px rgba(88,166,255,0.4); color: #58a6ff;
  }
  .stage-done     {
    background: #0d1117; border-color: #3fb950;
    box-shadow: 0 0 12px rgba(63,185,80,0.25); color: #3fb950;
  }

  /* ── Terminal log ── */
  .log-box {
    background: #010409; border: 1px solid #21262d;
    border-radius: 8px; padding: 14px;
    font-family: 'Courier New', monospace; font-size: 0.75rem;
    color: #39d353; max-height: 280px; overflow-y: auto;
    white-space: pre-wrap; word-break: break-all;
    line-height: 1.6;
  }

  /* ── Metrics ── */
  div[data-testid="metric-container"] {
    background: #0d1117; border: 1px solid #21262d;
    border-radius: 8px; padding: 10px;
  }

  /* ── Button ── */
  .stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: #fff; border: none; border-radius: 6px;
    font-weight: 700; letter-spacing: 0.05em;
    padding: 0.55rem 2rem; transition: all 0.2s;
    font-family: 'JetBrains Mono', monospace;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #2ea043, #3fb950);
    box-shadow: 0 0 16px rgba(63,185,80,0.5);
    transform: translateY(-1px);
  }

  /* ── File uploader ── */
  [data-testid="stFileUploader"] {
    background: #0d1117; border: 2px dashed #21262d;
    border-radius: 10px; padding: 8px;
  }
  [data-testid="stFileUploader"]:hover { border-color: #58a6ff; }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] { background: transparent; gap: 4px; }
  .stTabs [data-baseweb="tab"] {
    background: #0d1117; border: 1px solid #21262d;
    border-radius: 6px; color: #6e7681; font-size: 0.78rem;
  }
  .stTabs [aria-selected="true"] {
    background: #161b22 !important; border-color: #58a6ff !important;
    color: #58a6ff !important;
  }

  hr { border-color: #21262d; }
  a  { color: #58a6ff; text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* ── QR tab ── */
  .qr-card {
    background: #0d1117; border: 1px solid #30363d;
    border-radius: 12px; padding: 28px 32px;
    text-align: center; max-width: 420px; margin: 0 auto;
  }
  .qr-card img { border-radius: 8px; border: 4px solid #21262d; }
  .qr-title { font-size: 1rem; font-weight: 700; color: #e6edf3; margin-bottom: 6px; }
  .qr-sub   { font-size: 0.75rem; color: #6e7681; margin-bottom: 20px; }
  .qr-warn  {
    background: #2d1b00; border: 1px solid #ea580c;
    border-radius: 8px; padding: 10px 14px;
    font-size: 0.72rem; color: #fb923c; margin-top: 16px; text-align: left;
  }
  .qr-step  {
    background: #0d1117; border: 1px solid #21262d;
    border-radius: 8px; padding: 12px 16px; margin: 8px 0;
    font-size: 0.78rem; color: #8b949e; text-align: left;
    display: flex; align-items: flex-start; gap: 12px;
  }
  .qr-step-num {
    background: #1c2333; border: 1px solid #30363d;
    border-radius: 50%; width: 22px; height: 22px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 700; color: #58a6ff; flex-shrink: 0;
  }

  /* ── File preview card ── */
  .file-preview {
    background: #0d1117; border: 1px solid #30363d;
    border-radius: 10px; padding: 14px 16px;
    display: flex; align-items: center; gap: 16px;
    margin: 8px 0;
  }
  .file-preview-icon {
    font-size: 2rem; flex-shrink: 0;
    width: 48px; height: 48px;
    background: #161b22; border: 1px solid #21262d;
    border-radius: 8px; display: flex;
    align-items: center; justify-content: center;
  }
  .file-preview-info { flex: 1; min-width: 0; }
  .file-preview-name {
    font-size: 0.85rem; font-weight: 700; color: #e6edf3;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .file-preview-meta { font-size: 0.7rem; color: #6e7681; margin-top: 3px; }
  .file-preview-badge {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 4px; padding: 2px 8px;
    font-size: 0.65rem; color: #3fb950; flex-shrink: 0;
  }

  /* ── Compact section header ── */
  .section-header {
    font-size: 0.65rem !important; font-weight: 700; letter-spacing: 0.2em;
    color: #58a6ff; text-transform: uppercase;
    border-bottom: 1px solid #21262d; padding-bottom: 4px;
    margin: 14px 0 8px 0 !important;
  }

  /* ── Compact stage cards ── */
  .stage-card {
    padding: 10px 8px !important;
    margin: 2px 0 !important;
  }

  /* ── Empty state box ── */
  .empty-state {
    background: #0d1117; border: 1px dashed #21262d;
    border-radius: 10px; padding: 28px 16px;
    text-align: center; color: #484f58;
    font-size: 0.78rem; line-height: 1.8;
  }
  .empty-state-icon { font-size: 1.8rem; margin-bottom: 8px; }

  /* ── Vault ready banner ── */
  .vault-ready {
    background: #0d1117; border: 1px solid #3fb950;
    border-radius: 10px; padding: 12px 16px;
    box-shadow: 0 0 16px rgba(63,185,80,0.15);
    font-size: 0.78rem; color: #3fb950;
    display: flex; align-items: center; gap: 10px;
  }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────
GITHUB_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24">
<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385
.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61
-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084
1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605
-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176
0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405
2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91
1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015
2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
</svg>"""

with st.sidebar:
    # GitHub profile link at top
    st.markdown(
        f'<a class="gh-badge" href="https://github.com/aryadityad/" target="_blank">'
        f'{GITHUB_SVG}&nbsp;aryadityad</a>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-header">⚙ Configuration</div>', unsafe_allow_html=True)
    vault_dir    = st.text_input("Vault Output Directory", value="./shared_vault")
    pub_key_path = st.text_input("RSA Public Key Path",    value="public.pem")

    st.markdown('<div class="section-header">🔑 Key Management</div>', unsafe_allow_html=True)
    if st.button("Generate RSA-2048 Keypair", use_container_width=True):
        with st.spinner("Generating 2048-bit RSA keypair…"):
            try:
                pub, priv = generate_rsa_keypair(".")
                st.success("✔ Keypair generated")
                st.code(f"Public : {pub}\nPrivate: {priv}", language="bash")
                st.warning("⚠ Keep private.pem secret — never commit to git!")
            except Exception as exc:
                st.error(f"Failed: {exc}")

    st.markdown('<div class="section-header">ℹ About</div>', unsafe_allow_html=True)
    st.markdown(
        "<small style='color:#6e7681'>"
        "<b style='color:#c9d1d9'>Aegis Hotspot Vault</b><br>"
        "RSA-2048 + AES-256-GCM<br>"
        "Offline-first secure bubble<br><br>"
        "<b style='color:#c9d1d9'>Course:</b> Cryptography &amp; Network Security<br>"
        "<b style='color:#c9d1d9'>Reg:</b> 23BCE5056<br>"
        "<b style='color:#c9d1d9'>Institute:</b> VIT Chennai"
        "</small>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
#   MAIN CONTENT
# ══════════════════════════════════════════════════════════════

# ── Header ─────────────────────────────────────────────────────
hcol1, hcol2 = st.columns([3, 1])
with hcol1:
    st.markdown('<p class="aegis-title">🛡️ AEGIS HOTSPOT VAULT</p>', unsafe_allow_html=True)
    st.markdown('<p class="aegis-sub">RSA-2048 · AES-256-GCM · OFFLINE SECURE BUBBLE · VIT CHENNAI</p>', unsafe_allow_html=True)
with hcol2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<a class="gh-badge" href="https://github.com/aryadityad/Aeigs" target="_blank">'
        f'{GITHUB_SVG}&nbsp;View on GitHub</a>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────
tab_vault, tab_how, tab_crypto, tab_qr = st.tabs([
    "🚀  Vault a File",
    "📖  How It Works",
    "🔬  Cryptography Deep Dive",
    "📲  Key Transfer (QR)",
])


# ══════════════════════════════════════════════════════════════
#   TAB 1 — VAULT A FILE
# ══════════════════════════════════════════════════════════════
with tab_vault:
    col1, col2 = st.columns([1.4, 1])

    # ── Pipeline renderer ─────────────────────────────────────
    STAGES = [
        ("🔑", "KEY_GEN",        "AES-256 Key Gen"),
        ("🔐", "RSA_WRAP",       "RSA-2048 Wrap"),
        ("🔒", "AES_ENCRYPT",    "AES-GCM Encrypt"),
        ("📦", "VAULT_ASSEMBLY", "Vault Assembly"),
    ]

    def render_pipeline(active_stage=None, done_stages=[]):
        cols = st.columns(len(STAGES))
        for i, (icon, key, label) in enumerate(STAGES):
            if key in done_stages:
                cls, symbol = "stage-done",    "✔"
            elif key == active_stage:
                cls, symbol = "stage-active",  "⟳"
            else:
                cls, symbol = "stage-pending", "○"
            cols[i].markdown(
                f'<div class="stage-card {cls}">'
                f'<b style="font-size:1.2rem">{icon}</b><br>'
                f'<b>{symbol}</b><br>'
                f'<small>{label}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── File type icon map ───────────────────────────────────
    FILE_ICONS = {
        ".pdf":".pdf", ".png":"🖼", ".jpg":"🖼", ".jpeg":"🖼",
        ".gif":"🎞", ".mp4":"🎬", ".mkv":"🎬", ".mp3":"🎵",
        ".wav":"🎵", ".txt":"📄", ".docx":"📝", ".xlsx":"📊",
        ".pptx":"📊", ".zip":"🗜", ".apk":"📱", ".py":"🐍",
        ".csv":"📊",
    }
    FILE_LABELS = {
        ".pdf":"PDF Document", ".png":"PNG Image", ".jpg":"JPEG Image",
        ".jpeg":"JPEG Image", ".gif":"GIF Image", ".mp4":"MP4 Video",
        ".mkv":"MKV Video", ".mp3":"MP3 Audio", ".wav":"WAV Audio",
        ".txt":"Text File", ".docx":"Word Document", ".xlsx":"Excel Spreadsheet",
        ".pptx":"PowerPoint", ".zip":"ZIP Archive", ".apk":"Android APK",
        ".py":"Python Script", ".csv":"CSV Spreadsheet",
    }

    def _fmt_size(n):
        if n >= 1_048_576: return f"{n/1_048_576:.2f} MB"
        if n >= 1024:      return f"{n/1024:.1f} KB"
        return f"{n} B"

    with col1:
        st.markdown('<div class="section-header">📁 File Uploader</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Drop any file to encrypt", label_visibility="collapsed")

        # ── Live file preview ─────────────────────────────────
        preview_placeholder = st.empty()
        if uploaded is not None:
            ext   = Path(uploaded.name).suffix.lower()
            icon  = FILE_ICONS.get(ext, "📎")
            label = FILE_LABELS.get(ext, ext.lstrip(".").upper() + " File" if ext else "File")
            sz    = _fmt_size(uploaded.size)
            preview_placeholder.markdown(
                f'<div class="file-preview">'
                f'  <div class="file-preview-icon">{icon}</div>'
                f'  <div class="file-preview-info">'
                f'    <div class="file-preview-name">{uploaded.name}</div>'
                f'    <div class="file-preview-meta">{label} &nbsp;·&nbsp; {sz} &nbsp;·&nbsp; Ready to vault</div>'
                f'  </div>'
                f'  <div class="file-preview-badge">✔ LOADED</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            preview_placeholder.markdown(
                '<div class="empty-state">'
                '<div class="empty-state-icon">📂</div>'
                'Drop a file above to see preview<br>'
                '<span style="color:#30363d;font-size:0.7rem">PDF · Image · Video · Audio · Docs · Any file type</span>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-header">⚡ Live Encryption Pipeline</div>', unsafe_allow_html=True)
        pipeline_placeholder = st.empty()
        with pipeline_placeholder.container():
            render_pipeline()

        log_placeholder = st.empty()

    with col2:
        st.markdown('<div class="section-header">📊 Vault Metrics</div>', unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        m3, m4 = st.columns(2)
        metric_plaintext  = m1.empty()
        metric_ciphertext = m2.empty()
        metric_overhead   = m3.empty()
        metric_vault_size = m4.empty()
        metric_plaintext.metric("Plaintext",   "—")
        metric_ciphertext.metric("Ciphertext", "—")
        metric_overhead.metric("Overhead",     "—")
        metric_vault_size.metric("Vault Size",  "—")

        st.markdown('<div class="section-header">🖥 Live Hex Inspector</div>', unsafe_allow_html=True)
        hex_placeholder = st.empty()
        hex_placeholder.markdown(
            '<div class="empty-state" style="text-align:left;padding:16px">'
            '<div class="empty-state-icon" style="font-size:1.2rem">💻</div>'
            '<span style="color:#39d353;font-family:Courier New,monospace;font-size:0.72rem">'
            '// Waiting for encryption run…<br>'
            '// AES key · RSA modulus · nonce · auth tag<br>'
            '// will appear here in real time'
            '</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Run button ─────────────────────────────────────────────
    st.markdown("")
    run_col, info_col = st.columns([1, 3])
    run_btn = run_col.button("🚀  Vault It!", use_container_width=True)
    if uploaded and not run_btn:
        info_col.markdown(
            f'<div style="padding:10px 0;color:#6e7681;font-size:0.75rem">'
            f'Ready to encrypt <b style="color:#e6edf3">{uploaded.name}</b> '
            f'({_fmt_size(uploaded.size)}) → '
            f'<span style="color:#58a6ff">RSA-2048 + AES-256-GCM</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Encryption logic ───────────────────────────────────────
    if run_btn:
        if uploaded is None:
            st.warning("⚠️  Please upload a file first.")
            st.stop()
        if not Path(pub_key_path).exists():
            st.error("❌  RSA public key not found — generate it in the sidebar first.")
            st.stop()

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(uploaded.name).suffix
        ) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        logs  = []
        done  = []
        state = {"active": None}

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
            time.sleep(0.5)

        try:
            with st.spinner("Sealing vault…"):
                vault_path, meta = encrypt_file(
                    plaintext_path  = tmp_path,
                    public_key_path = pub_key_path,
                    output_dir      = vault_dir,
                    progress_cb     = progress,
                )

            if state["active"]:
                done.append(state["active"])
            with pipeline_placeholder.container():
                render_pipeline(active_stage=None, done_stages=done)

            push_log("<span style='color:#3fb950'>✔ Vault sealed successfully!</span>")

            # Metrics
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

            # Hex inspector
            hex_lines = [
                "<b style='color:#58a6ff'>// ═══ AEGIS VAULT INSPECTOR ═══</b>",
                f"<b style='color:#e3b341'>File       :</b> {uploaded.name}",
                f"<b style='color:#e3b341'>Vault      :</b> {vault_path}",
                "",
                "<b style='color:#58a6ff'>// AES-256-GCM Session Key  (32 bytes)</b>",
                f"<span style='color:#39d353'>{meta['aes_key_hex']}</span>",
                "<b style='color:#6e7681'>// ↑ Random per-file. Encrypted by RSA before storage.</b>",
                "",
                "<b style='color:#58a6ff'>// RSA-2048 Public Modulus  (truncated to 48 B)</b>",
                f"<span style='color:#d2a8ff'>{meta['rsa_pub_hex'][:96]}…</span>",
                "<b style='color:#6e7681'>// ↑ Used to wrap the AES key above.</b>",
                "",
                "<b style='color:#58a6ff'>// AES-GCM Nonce  (16 bytes)</b>",
                f"<span style='color:#ffa657'>{meta['nonce_hex']}</span>",
                "<b style='color:#6e7681'>// ↑ Random. Ensures same plaintext → different ciphertext every time.</b>",
                "",
                "<b style='color:#58a6ff'>// GCM Authentication Tag  (16 bytes)</b>",
                f"<span style='color:#ff7b72'>{meta['tag_hex']}</span>",
                "<b style='color:#6e7681'>// ↑ Any tampered byte → decryption fails immediately.</b>",
                "",
                "<b style='color:#3fb950'>// VAULT BINARY LAYOUT</b>",
                "  <span style='color:#e3b341'>[Magic 8B]</span> [Ver 1B] [Fname len 2B] [Filename NB]",
                f"  <span style='color:#d2a8ff'>[RSA-Wrapped AES Key  : 256 B]</span>",
                f"  <span style='color:#ffa657'>[Nonce                :  16 B]</span>",
                f"  <span style='color:#ff7b72'>[Auth Tag             :  16 B]</span>",
                f"  <span style='color:#39d353'>[Ciphertext           : {cipher_sz} B]</span>",
            ]
            hex_placeholder.markdown(
                f'<div class="log-box">{"<br>".join(hex_lines)}</div>',
                unsafe_allow_html=True,
            )

            st.success(f"🛡️  Vault ready at `{vault_path}` — pick it up via the FTP server!")

        except Exception as exc:
            st.error(f"❌  Encryption failed: {exc}")
            push_log(f"<span style='color:#ff7b72'>ERROR: {exc}</span>")
        finally:
            os.unlink(tmp_path)


# ══════════════════════════════════════════════════════════════
#   TAB 2 — HOW IT WORKS
# ══════════════════════════════════════════════════════════════
with tab_how:
    st.markdown('<div class="section-header">🏗 System Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="explainer">'
        '<b>Aegis Hotspot Vault</b> creates an offline-first <b>"Secure Bubble"</b> using your laptop\'s '
        'Wi-Fi hotspot as a private local network. Files are cryptographically sealed on the laptop and '
        'transferred to an Android phone running <b>Termux</b> over FTP — with <b>zero internet involvement</b>.'
        '<br><br>'
        'The system uses a <b>hybrid encryption scheme</b>: a fast symmetric cipher (AES-256-GCM) encrypts '
        'the file, and a slow asymmetric cipher (RSA-2048) securely transports the encryption key. '
        'This gives you the speed of symmetric encryption with the key-exchange security of asymmetric encryption.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-header">⚙ How Each Component Works</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="how-grid">
  <div class="how-card" data-step="1">
    <div class="how-icon">🔑</div>
    <div class="how-title">crypto_core.py</div>
    <div class="how-desc">The cryptographic engine. Generates RSA keypairs, performs AES-256-GCM encryption, wraps the session key with RSA-OAEP, and assembles the binary vault file.</div>
    <span class="how-tag">PyCryptodome</span>
  </div>
  <div class="how-card" data-step="2">
    <div class="how-icon">🖥️</div>
    <div class="how-title">app.py</div>
    <div class="how-desc">This Streamlit dashboard. Provides drag-and-drop upload, animates the live encryption pipeline, and shows real hex outputs of cryptographic values.</div>
    <span class="how-tag">Streamlit</span>
  </div>
  <div class="how-card" data-step="3">
    <div class="how-icon">📡</div>
    <div class="how-title">server.py</div>
    <div class="how-desc">An FTP server bound to your hotspot IP on port 2121. Serves the shared_vault/ folder. All sessions are audit-logged with timestamps and source IPs.</div>
    <span class="how-tag">pyftpdlib</span>
  </div>
  <div class="how-card" data-step="4">
    <div class="how-icon">📱</div>
    <div class="how-title">client.py</div>
    <div class="how-desc">Runs in Termux on Android. Connects to the laptop over FTP, downloads the vault, decrypts it using the private key, and opens the file.</div>
    <span class="how-tag">Termux</span>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">🔄 Transfer Flow</div>', unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.markdown(
            '<div class="explainer">'
            '<b style="color:#58a6ff">① On the Laptop</b><br><br>'
            '1. Upload file in the dashboard<br>'
            '2. <code>KEY_GEN</code> — random 256-bit AES key created<br>'
            '3. <code>RSA_WRAP</code> — AES key encrypted with <code>public.pem</code><br>'
            '4. <code>AES_ENCRYPT</code> — file encrypted + auth tag generated<br>'
            '5. <code>VAULT_ASSEMBLY</code> — all components written to <code>.vault</code> file<br>'
            '6. FTP server serves the vault on port 2121'
            '</div>',
            unsafe_allow_html=True,
        )
    with fc2:
        st.markdown(
            '<div class="explainer" style="border-left-color:#e3b341">'
            '<b style="color:#e3b341">② Over the Hotspot</b><br><br>'
            'The phone connects to the laptop\'s Wi-Fi hotspot.<br><br>'
            'Gateway IP: <code>192.168.137.1</code><br>'
            'FTP port: <code>2121</code><br><br>'
            'The <code>.vault</code> file travels over the local network. '
            'Even if intercepted, the ciphertext is '
            '<b>computationally indistinguishable from random bytes</b> '
            'without the private key.'
            '</div>',
            unsafe_allow_html=True,
        )
    with fc3:
        st.markdown(
            '<div class="explainer" style="border-left-color:#3fb950">'
            '<b style="color:#3fb950">③ On the Phone</b><br><br>'
            '1. <code>client.py</code> connects to FTP server<br>'
            '2. Downloads the <code>.vault</code> file<br>'
            '3. Parses header → reads original filename<br>'
            '4. Decrypts AES key using <code>private.pem</code><br>'
            '5. Decrypts file with AES-GCM<br>'
            '6. Verifies 128-bit auth tag — detects tampering<br>'
            '7. Saves with original filename, prompts to open'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-header">🔒 Security Guarantees</div>', unsafe_allow_html=True)
    sc1, sc2, sc3, sc4 = st.columns(4)
    for col, icon, title, body in [
        (sc1, "🔐", "Confidentiality",  "AES-256-GCM ciphertext is indistinguishable from random data. An eavesdropper sees only noise."),
        (sc2, "✅", "Integrity",         "128-bit GCM auth tag. Any single tampered byte causes decryption to fail immediately."),
        (sc3, "🔑", "Key Security",      "RSA-2048 OAEP. Breaking it requires factoring a 2048-bit semiprime — infeasible with current hardware."),
        (sc4, "🎲", "Freshness",         "Per-file random 128-bit nonce. Encrypting the same file twice produces completely different ciphertext."),
    ]:
        col.markdown(
            f'<div class="how-card">'
            f'<div class="how-icon">{icon}</div>'
            f'<div class="how-title">{title}</div>'
            f'<div class="how-desc">{body}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════
#   TAB 3 — CRYPTOGRAPHY DEEP DIVE
# ══════════════════════════════════════════════════════════════
with tab_crypto:
    st.markdown('<div class="section-header">🔐 RSA-2048 OAEP — Asymmetric Key Transport</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="explainer">'
        '<b>RSA (Rivest–Shamir–Adleman)</b> is a public-key cryptosystem based on the mathematical '
        'difficulty of factoring the product of two large prime numbers.<br><br>'
        '• Key size: <code>2048 bits</code> — NIST-recommended minimum through 2030<br>'
        '• Padding: <code>OAEP (Optimal Asymmetric Encryption Padding)</code> with SHA-1 — '
        'semantically secure; resistant to chosen-ciphertext attacks unlike raw PKCS#1 v1.5<br>'
        '• Use in Aegis: encrypts the 32-byte AES session key into a <code>256-byte</code> wrapped block.<br><br>'
        '<b>Why not RSA for the whole file?</b> RSA can only encrypt data smaller than its key size '
        'and is ~1000× slower than AES. It is used only for the small session key.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-header">🔒 AES-256-GCM — Authenticated Encryption</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="explainer">'
        '<b>AES-GCM (Galois/Counter Mode)</b> is an <b>AEAD</b> (Authenticated Encryption with Associated Data) cipher. '
        'It combines two operations in one pass:<br><br>'
        '• <b>CTR mode encryption</b> — turns AES into a stream cipher; fast, parallelisable, no padding needed<br>'
        '• <b>GHASH authentication</b> — computes a 128-bit MAC over the ciphertext using Galois field multiplication<br><br>'
        'Key size: <code>256 bits</code> (2²⁵⁶ possible keys — more atoms than exist in the observable universe)<br>'
        'Nonce: <code>128 bits</code>, random per file — guarantees ciphertext uniqueness<br>'
        'Auth tag: <code>128 bits</code> — any bit-flip anywhere in the ciphertext invalidates the tag'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-header">📦 Vault Binary Format</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="vault-format">'
        'Offset    Size        Field               Value / Notes\n'
        '──────    ────        ─────               ─────────────────────────────────\n'
        '0         8 bytes     Magic               ASCII "AEGISVLT"  — file identifier\n'
        '8         1 byte      Version             0x01\n'
        '9         2 bytes     Filename Length     Big-endian uint16\n'
        '11        N bytes     Original Filename   UTF-8  e.g. "report.pdf"\n'
        '11+N    256 bytes     RSA-Wrapped Key     PKCS1-OAEP(aes_key, public.pem)\n'
        '267+N    16 bytes     GCM Nonce           Random per file\n'
        '283+N    16 bytes     GCM Auth Tag        128-bit integrity tag\n'
        '299+N   variable      Ciphertext          AES-256-GCM(plaintext, aes_key)\n'
        '\n'
        'Fixed overhead = 8+1+2+256+16+16 = 299 bytes + len(filename)'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-header">🔄 Encryption & Decryption Pseudocode</div>', unsafe_allow_html=True)
    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**Encryption (laptop)**")
        st.code("""\
# Stage 1 — Key Gen
aes_key = os.urandom(32)          # 256-bit

# Stage 2 — RSA Wrap
pub  = RSA.import_key(public.pem)
oaep = PKCS1_OAEP.new(pub)
wrapped_key = oaep.encrypt(aes_key)   # 256 B

# Stage 3 — AES-256-GCM
nonce  = os.urandom(16)
cipher = AES.new(aes_key, MODE_GCM, nonce=nonce)
ciphertext, tag = cipher.encrypt_and_digest(
    plaintext
)

# Stage 4 — Vault Assembly
vault = (
    b"AEGISVLT"          # magic
  + b"\\x01"              # version
  + len(fname).to_bytes(2,"big")
  + fname.encode()
  + wrapped_key           # 256 B
  + nonce                 # 16 B
  + tag                   # 16 B
  + ciphertext            # variable
)
""", language="python")
    with dc2:
        st.markdown("**Decryption (Termux)**")
        st.code("""\
# Parse vault header
magic        = vault[0:8]
fname_len    = int.from_bytes(vault[9:11],"big")
filename     = vault[11:11+fname_len]
wrapped_key  = vault[11+N : 267+N]
nonce        = vault[267+N : 283+N]
tag          = vault[283+N : 299+N]
ciphertext   = vault[299+N :]

# RSA Unwrap
priv  = RSA.import_key(private.pem)
oaep  = PKCS1_OAEP.new(priv)
aes_key = oaep.decrypt(wrapped_key)

# AES-256-GCM + Auth Verify
cipher = AES.new(aes_key, MODE_GCM, nonce=nonce)
plaintext = cipher.decrypt_and_verify(
    ciphertext, tag   # raises on tamper ✗
)

# Save with original name
open(filename, "wb").write(plaintext)
""", language="python")

    st.markdown('<div class="section-header">📐 Why This Scheme Is Secure</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="explainer">'
        '<b>Semantic Security (IND-CPA):</b> RSA-OAEP is provably IND-CPA secure under the RSA assumption. '
        'AES-GCM is IND-CPA secure under the assumption that AES is a pseudorandom permutation. '
        'An attacker who intercepts the vault cannot distinguish the ciphertext from a random string.<br><br>'
        '<b>Integrity (IND-CCA):</b> The GCM auth tag makes the scheme IND-CCA2 secure. '
        'Any chosen-ciphertext attack that modifies the vault will be detected and rejected before decryption.<br><br>'
        '<b>Forward Secrecy (partial):</b> Each file uses a freshly generated AES session key. '
        'Compromising one vault\'s session key reveals nothing about other vaults.'
        '</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
#   TAB 4 — QR KEY TRANSFER
# ══════════════════════════════════════════════════════════════
with tab_qr:
    st.markdown('<div class="section-header">📲 Transfer Private Key to Phone via QR Code</div>', unsafe_allow_html=True)

    qr_col, info_col = st.columns([1, 1.2])

    with qr_col:
        priv_key_path = "private.pem"
        if not Path(priv_key_path).exists():
            st.markdown(
                '<div class="empty-state">'
                '<div class="empty-state-icon">🔑</div>'
                'No private.pem found.<br>'
                '<span style="color:#30363d;font-size:0.7rem">Generate a keypair in the sidebar first.</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            try:
                import qrcode
                import qrcode.image.pil

                priv_pem = Path(priv_key_path).read_text().strip()

                # Generate QR
                qr = qrcode.QRCode(
                    version      = None,
                    error_correction = qrcode.constants.ERROR_CORRECT_L,
                    box_size     = 6,
                    border       = 3,
                )
                qr.add_data(priv_pem)
                qr.make(fit=True)
                img = qr.make_image(fill_color="#c9d1d9", back_color="#0d1117")

                # Convert to base64 for display
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()

                st.markdown(
                    f'<div class="qr-card">'
                    f'<div class="qr-title">🔑 private.pem QR Code</div>'
                    f'<div class="qr-sub">Scan with Termux QR scanner — no USB needed</div>'
                    f'<img src="data:image/png;base64,{b64}" width="300"/>'
                    f'<div class="qr-warn">'
                    f'⚠ <b>Security Warning:</b> This QR contains your RSA private key. '
                    f'Only scan in a private environment. Anyone who scans this can decrypt your vaults.'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            except ImportError:
                st.error("qrcode library not installed. Run: pip install qrcode[pil]")
            except Exception as exc:
                st.error(f"QR generation failed: {exc}")

    with info_col:
        st.markdown('<div class="section-header">📋 How to Scan on the Phone</div>', unsafe_allow_html=True)
        for step_num, step_text in [
            ("1", "Install the QR scanner in Termux:"),
            ("2", "Run the scanner command:"),
            ("3", "Point camera at the QR code on your screen"),
            ("4", "The private key is saved automatically to ~/private.pem"),
            ("5", "Run client.py — it will find and use the key"),
        ]:
            st.markdown(
                f'<div class="qr-step">'
                f'<div class="qr-step-num">{step_num}</div>'
                f'<div>{step_text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-header">💻 Termux Commands</div>', unsafe_allow_html=True)
        st.code("pkg install termux-tools", language="bash")
        st.code("termux-camera-photo -c 0 qr.jpg\nzbarimg qr.jpg > ~/private.pem", language="bash")

        st.markdown('<div class="section-header">ℹ Why QR Transfer?</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="explainer">'
            'Transferring <code>private.pem</code> via USB requires enabling MTP mode, '
            'navigating file managers, and manually moving the file. '
            '<br><br>'
            'QR transfer is instant — point the camera, done. No cables, no file managers, '
            'no risk of copying the key to the wrong location.'
            '<br><br>'
            '<b>The QR code encodes the full PEM text</b> of the private key, which is then '
            'written directly to <code>~/private.pem</code> on the phone.'
            '</div>',
            unsafe_allow_html=True,
        )

        # Key fingerprint for verification
        if Path("private.pem").exists():
            try:
                from Crypto.PublicKey import RSA
                import hashlib
                key_data = Path("private.pem").read_bytes()
                fingerprint = hashlib.sha256(key_data).hexdigest()
                st.markdown('<div class="section-header">🔍 Key Fingerprint (SHA-256)</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="log-box" style="font-size:0.7rem">'
                    f'// Verify this matches on both devices after transfer<br>'
                    f'<span style="color:#39d353">{fingerprint[:32]}</span><br>'
                    f'<span style="color:#39d353">{fingerprint[32:]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            except Exception:
                pass