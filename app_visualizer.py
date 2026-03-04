import streamlit as st
import crypto_engine
import os
import io
import contextlib

# Configure Streamlit page layout
st.set_page_config(page_title="Aegis-Hotspot Vault Visualizer", layout="wide", page_icon="🛡️", initial_sidebar_state="expanded")

# Sidebar for Author and GitHub Links
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/shield.png", width=80)
    st.title("Aegis-Hotspot Vault")
    st.markdown("### By Aryaditya Deshmukh")
    st.markdown("**Reg No**: 23BCE5056")
    st.markdown("[![GitHub](https://img.icons8.com/material-outlined/24/000000/github.png) View on GitHub](https://github.com/aryadityad/Aeigis)")
    st.divider()
    st.markdown("### 🔐 How it Works:")
    st.markdown("""
    **1. RSA-2048 (Asymmetric)**
    Generates a secure keypair. The Public Key encrypts the AES Session Key, ensuring only the Phone's Private Key can unlock it.
    
    **2. AES-256-GCM (Symmetric)**
    Encrypts the actual file blazing fast. The *GCM mode* produces an Authentication Tag to prevent any Wi-Fi tampering!
    """)
    st.info("Zero-Knowledge Principle: Private keys NEVER leave the local device.")

st.title("🛡️ Aegis-Hotspot Vault")
st.markdown("**Real-Time Cryptographic Handshake Visualizer**")
st.info("🎓 **Academic Project**: Built for the *Cryptography and Network Security* course to practically explain, visualize, and apply real-world cryptographic architectures (Hybrid RSA + AES-GCM).")
st.write("This dashboard visualizes the core encryption and decapsulation process happening under the hood.")
st.divider()

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("🛠️ Control Panel")
    st.write("Control the cryptographic flow:")
    
    action = st.radio("Select Operation", ["1. Generate RSA Keys", "2. Encrypt Data (Laptop -> Vault)", "3. Decrypt Data (Vault -> Phone)"])
    
    file_content = st.text_area("File Content Payload", "Enter highly confidential Project Data here...", height=150)
    
    execute_clicked = st.button("🚀 Execute Cryptographic Operation", type="primary")

with col2:
    st.subheader("🖥️ Live Cryptographic Console")
    st.markdown("Displays the console logs representing the protocol actions in real-time.")
    console_view = st.empty()
    
# Process User Execution
if execute_clicked:
    # We will capture the stdout (print statements) from crypto_engine.py
    log_capture = io.StringIO()
    
    with st.spinner("Executing secure sequence..."):
        with contextlib.redirect_stdout(log_capture):
            try:
                if "Generate" in action:
                    print("[Operation] Initializing RSA Asymmetric Engine...")
                    crypto_engine.generate_keys()
                    print("\n[Success] Generated public.pem and private.pem locally.")
                    
                elif "Encrypt" in action:
                    if not os.path.exists("public.pem"):
                        print("[Error] Security Fault: 'public.pem' not found. Please generate keys first.")
                    else:
                        print("[Operation] Initializing Encrypt Sequence...")
                        # Save the text area to a dummy local file for the crypto_engine to read
                        with open("demo_input.txt", "w") as f_in:
                            f_in.write(file_content)
                            
                        crypto_engine.encrypt_file("demo_input.txt", "demo_vault.vault", "public.pem")
                        
                elif "Decrypt" in action:
                    if not os.path.exists("private.pem") or not os.path.exists("demo_vault.vault"):
                        print("[Error] Security Fault: Missing 'private.pem' or 'demo_vault.vault'.")
                        print("Please run Generate Keys and Encrypt Data steps first.")
                    else:
                        print("[Operation] Initializing Decrypt Sequence...")
                        
                        crypto_engine.decrypt_file("demo_vault.vault", "demo_output.txt", "private.pem")
                        
                        # Read the decrypted output to prove it to the UI
                        with open("demo_output.txt", "r") as f_out:
                            result = f_out.read()
                            
                        print(f"\n[Success] File successfully decrypted. Extracted Payload:")
                        print(f"--------------------------------------------------")
                        print(f"{result}")
                        print(f"--------------------------------------------------")
                        
            except ValueError as ve:
                print(f"[CRITICAL INTEGRITY FAILURE] {str(ve)}")
            except Exception as e:
                print(f"[Exception] System Fault: {str(e)}")
                
    # Display the captured output nicely on the console visualizer
    output_text = log_capture.getvalue()
    console_view.code(output_text, language="text")
    st.toast("Operation Complete!")
else:
    # Default waiting text
    console_view.code("Waiting for cryptographic operation...\nClick 'Execute' on the control panel to begin.", language="text")
