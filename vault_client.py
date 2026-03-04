import ftplib
import os
import sys
from crypto_engine import decrypt_file

def download_and_decrypt(server_ip, port, username, password, remote_filename, local_filename, private_key_file):
    print(f"Connecting to Gateway FTP Server at {server_ip}:{port}...")
    
    try:
        # Connect to the localized FTP server hosted on the laptop hotspot
        ftp = ftplib.FTP()
        ftp.connect(server_ip, port)
        ftp.login(username, password)
        print("Successfully authenticated with Aegis-Hotspot Vault FTP server.")
        
        # Download the .vault file securely over the localized link
        # Even if the Wi-Fi link is plaintext or unencrypted, the file itself is highly encrypted (AES-GCM)
        print(f"Downloading {remote_filename} to {local_filename}...")
        with open(local_filename, "wb") as f:
            ftp.retrbinary(f"RETR {remote_filename}", f.write)
            
        print("Download complete.")
        ftp.quit()
        
    except Exception as e:
        print(f"FTP Network Error: {e}")
        sys.exit(1)
        
    print(f"\n[Aegis-Vault] Triggering decapsulation of {local_filename} using RSA Private Key...")
    
    # Decrypt the file
    try:
        decrypted_filename = local_filename.replace(".vault", "")
        if decrypted_filename == local_filename:
            decrypted_filename += ".decrypted"
            
        # This function invokes the Integrity Guard: verifies GCM Auth Tag
        # If the file has been tampered with or corrupted, it will throw a ValueError
        decrypt_file(local_filename, decrypted_filename, private_key_file)
        
        print(f"SUCCESS! Integrity verified and file decrypted to: {decrypted_filename}")
        
    except ValueError as ve:
        # Catch MAC check failures specifically
        if "MAC check failed" in str(ve):
            print("\n!!! SECURITY ALERT - INTEGRITY COMPROMISED !!!")
            print("The file's internal authentication tag (GCM) failed verification.")
            print("The file may have been altered in transit by an adversary. Operations halted.")
            # Remove the corrupted/tampered file as a safety precaution
            if os.path.exists(decrypted_filename):
                os.remove(decrypted_filename)
        else:
            print(f"Decryption failed due to invalid data: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during decryption: {e}")

if __name__ == "__main__":
    SERVER_IP = "192.168.137.1"
    PORT = 2121
    USERNAME = "aryaditya"
    PASSWORD = "vit"
    
    # Provide usage instructions if argument not provided
    if len(sys.argv) < 2:
        print("Usage: python vault_client.py <remote_vault_filename>")
        print("Example: python vault_client.py secret_document.vault")
        sys.exit(1)
        
    REMOTE_FILE = sys.argv[1]
    LOCAL_FILE = f"downloaded_{REMOTE_FILE}"
    PRIVATE_KEY = "private.pem" # Phone's RSA Private Key (must exist locally)
    
    if not os.path.exists(PRIVATE_KEY):
        print(f"Error: '{PRIVATE_KEY}' not found in current directory.")
        print("Please ensure the Termux environment has the private RSA key.")
        sys.exit(1)
        
    download_and_decrypt(SERVER_IP, PORT, USERNAME, PASSWORD, REMOTE_FILE, LOCAL_FILE, PRIVATE_KEY)
