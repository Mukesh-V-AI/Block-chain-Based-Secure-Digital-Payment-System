"""
Cryptographic Utilities Module

This module provides the core cryptographic functions required by the blockchain.
It utilizes the `ecdsa` library to perform secp256k1 operations, simulating 
standard cryptocurrency signature verification and wallet generation.
"""

import ecdsa
import hashlib
import base64

def generate_key_pair():
    """
    Generates a secure asymmetric secp256k1 key pair.
    
    Returns:
        tuple: (private_key_hex, public_key_hex)
    """
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    return sk.to_string().hex(), vk.to_string().hex()

def generate_wallet_address(pub_hex: str) -> str:
    """
    Derives a deterministic wallet address from a given public key hex.
    Similar to Ethereum's approach, it hashes the public key and trims the result.
    
    Args:
        pub_hex (str): The public key in hexadecimal format.
        
    Returns:
        str: A wallet address starting with '0x'
    """
    sha = hashlib.sha256(pub_hex.encode()).hexdigest()
    return "0x" + sha[:40]

def sign_data(private_key_hex: str, data: str) -> str:
    """
    Signs a string of data using the provided private key.
    Outputs a base64 encoded DER signature.
    
    Args:
        private_key_hex (str): The signer's private key in hex.
        data (str): The payload to be signed.
        
    Returns:
        str: Base64 encoded digital signature.
    """
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
    signature = sk.sign(data.encode(), hashfunc=hashlib.sha256, sigencode=ecdsa.util.sigencode_der)
    return base64.b64encode(signature).decode()

def verify_signature(public_key_hex: str, signature_b64: str, data: str) -> bool:
    """
    Verifies a digital signature against the original data and the signer's public key.
    
    Args:
        public_key_hex (str): The expected signer's public key in hex.
        signature_b64 (str): The base64 encoded DER signature.
        data (str): The original signed payload.
        
    Returns:
        bool: True if signature is valid, False otherwise.
    """
    try:
        vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=ecdsa.SECP256k1)
        sig = base64.b64decode(signature_b64)
        return vk.verify(sig, data.encode(), hashfunc=hashlib.sha256, sigdecode=ecdsa.util.sigdecode_der)
    except Exception:
        return False

def hash_data(data: str) -> str:
    """
    Computes a SHA-256 hash of the input string.
    
    Args:
        data (str): The data to hash.
        
    Returns:
        str: The SHA-256 hex digest.
    """
    return hashlib.sha256(data.encode()).hexdigest()
