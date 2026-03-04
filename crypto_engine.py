import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes

def generate_keys(private_out="private.pem", public_out="public.pem"):
    """
    Generate RSA-2048 keys.
    [VIVA VOCE NOTE]
    We use RSA-2048 because it provides a strong level of asymmetric security suitable for modern applications.
    The public key is used by the laptop to encrypt the symmetric session key, and the private key is
    kept strictly on the client (phone) to decrypt it.
    """
    key = RSA.generate(2048)
    with open(private_out, "wb") as f:
        f.write(key.export_key())
    with open(public_out, "wb") as f:
        f.write(key.publickey().export_key())

def package_vault(encrypted_aes_key, nonce, tag, ciphertext, output_file):
    """
    Bundles the cryptographic components into a single binary .vault file.
    Format Structure:
    - [RSA-encrypted Key (256 bytes)] 
    - [16-byte Nonce]
    - [16-byte GCM Auth Tag]
    - [Ciphertext] (variable length)
    """
    with open(output_file, "wb") as f:
        f.write(encrypted_aes_key)
        f.write(nonce)
        f.write(tag)
        f.write(ciphertext)

def encrypt_file(input_file, output_file, public_key_file):
    """
    Encrypts a file using a hybrid cryptographic approach ensuring maximum security and speed.
    """
    print(f"\n[Security Engine] Starting encryption process for '{input_file}'...")
    
    # 1. Generate a random AES-256 key (32 bytes)
    # [VIVA VOCE NOTE] AES-256 is symmetrically extremely fast for bulk data, unlike RSA which is slow.
    print("[Security Engine] 1. Generating a random 32-byte AES-256 session key...")
    aes_key = get_random_bytes(32)
    
    # 2. Encrypt the AES key with the recipient's RSA Public Key using PKCS1_OAEP
    # [VIVA VOCE NOTE] PKCS1_OAEP adds optimal asymmetric encryption padding. This randomness
    # prevents chosen ciphertext attacks and ensures the same key ciphertext isn't generated twice.
    print(f"[Security Engine] 2. Encrypting AES session key with recipient's RSA Public Key ({public_key_file}) using PKCS1_OAEP...")
    recipient_key = RSA.import_key(open(public_key_file).read())
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    encrypted_aes_key = cipher_rsa.encrypt(aes_key)
    
    # 3. Encrypt the actual file data using AES-256-GCM
    # [VIVA VOCE NOTE] GCM (Galois/Counter Mode) provides BOTH data confidentiality and authenticity.
    # It generates an authentication tag that guarantees the file wasn't tampered with over the hotspot.
    print("[Security Engine] 3. Reading plaintext data and encrypting with AES-256-GCM...")
    with open(input_file, "rb") as f:
        data = f.read()
        
    cipher_aes = AES.new(aes_key, AES.MODE_GCM)
    ciphertext, tag = cipher_aes.encrypt_and_digest(data)
    print(f"[Security Engine]    -> Ciphertext generated ({len(ciphertext)} bytes).")
    print("[Security Engine]    -> 16-byte GCM Authentication Tag derived for Integrity checking.")
    
    # 4. Bundle everything into the .vault file
    print(f"[Security Engine] 4. Packaging Encrypted Key, Nonce, Auth Tag, and Ciphertext into '{output_file}'...")
    package_vault(encrypted_aes_key, cipher_aes.nonce, tag, ciphertext, output_file)
    print(f"[Security Engine] Encryption complete! Secure vault created at '{output_file}'.\n")

def unpackage_vault(input_file):
    """
    Extracts the components from the .vault binary file.
    Assumes RSA-2048 (256 bytes) and AES-GCM (16-byte nonce, 16-byte tag).
    """
    with open(input_file, "rb") as f:
        encrypted_aes_key = f.read(256)
        nonce = f.read(16)
        tag = f.read(16)
        ciphertext = f.read()
    return encrypted_aes_key, nonce, tag, ciphertext

def decrypt_file(input_file, output_file, private_key_file):
    """
    Decrypts the .vault file and verifies its integrity.
    If the authentication tag does not match (e.g., file altered by malicious actor in the middle),
    it stops and raises a ValueError.
    """
    print(f"\n[Security Engine] Starting decryption and verification process for '{input_file}'...")
    
    print("[Security Engine] 1. Unpackaging binary vault format to extract components...")
    encrypted_aes_key, nonce, tag, ciphertext = unpackage_vault(input_file)
    
    # 1. Decrypt the AES key using the RSA Private Key
    print(f"[Security Engine] 2. Decrypting the AES session key using the local RSA Private Key ({private_key_file})...")
    private_key = RSA.import_key(open(private_key_file).read())
    cipher_rsa = PKCS1_OAEP.new(private_key)
    aes_key = cipher_rsa.decrypt(encrypted_aes_key)
    
    # 2. Decrypt the data using AES-GCM and verify authenticity
    print("[Security Engine] 3. Initializing AES-GCM cipher with decrypted session key and extracted nonce...")
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    
    # [VIVA VOCE NOTE] Integrity Guard: This automatically computes the MAC of the ciphertext
    # and compares it with the saved `tag`. Raises ValueError("MAC check failed") if tampered.
    print("[Security Engine] 4. Decrypting ciphertext and verifying GCM Authentication Tag (Integrity Guard)...")
    decrypted_data = cipher_aes.decrypt_and_verify(ciphertext, tag)
    print("[Security Engine]    -> Integrity Guard Verified! The file is authentic and unaltered.")
    
    print(f"[Security Engine] 5. Writing pristine decrypted data to '{output_file}'...")
    with open(output_file, "wb") as f:
        f.write(decrypted_data)
    print(f"[Security Engine] Decryption block successfully completed.\n")

if __name__ == "__main__":
    # Test execution for Viva voce / Demo purposes
    print("Generating RSA keys for initial setup...")
    generate_keys()
    
    # Generate a dummy file for the demo
    with open("secret_document.txt", "w") as f:
        f.write("Aegis-Hotspot Vault Top Secret Data")
        
    print("Encrypting secret_document.txt -> secret_document.vault")
    encrypt_file("secret_document.txt", "secret_document.vault", "public.pem")
    
    print("Decrypting secret_document.vault -> secret_document.decrypted")
    decrypt_file("secret_document.vault", "secret_document.decrypted", "private.pem")
    
    print("Self-test complete. Check for secret_document.decrypted locally.")
