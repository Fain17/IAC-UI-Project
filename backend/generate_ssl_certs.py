#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for WSS development.
Run this script to create the necessary certificates for secure WebSocket connections.
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_ssl_certificates():
    """Generate self-signed SSL certificates for development."""
    
    # Create certs directory if it doesn't exist
    certs_dir = Path("certs")
    certs_dir.mkdir(exist_ok=True)
    
    key_file = certs_dir / "key.pem"
    cert_file = certs_dir / "cert.pem"
    
    # Check if certificates already exist
    if key_file.exists() and cert_file.exists():
        print("✅ SSL certificates already exist in 'certs' directory")
        print(f"   Key: {key_file}")
        print(f"   Cert: {cert_file}")
        return True
    
    print("🔐 Generating self-signed SSL certificates for WSS...")
    
    try:
        # Generate private key
        subprocess.run([
            "openssl", "genrsa", "-out", str(key_file), "2048"
        ], check=True, capture_output=True)
        
        # Generate certificate
        subprocess.run([
            "openssl", "req", "-new", "-x509", "-key", str(key_file),
            "-out", str(cert_file), "-days", "365", "-subj",
            "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        ], check=True, capture_output=True)
        
        print("✅ SSL certificates generated successfully!")
        print(f"   Key: {key_file}")
        print(f"   Cert: {cert_file}")
        print("\n🚀 You can now start the server with WSS support:")
        print("   python app/main.py")
        print("\n🔗 Frontend should connect using:")
        print("   wss://localhost:8000/ws/token-monitor?token=...")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating certificates: {e}")
        print("Make sure OpenSSL is installed on your system.")
        return False
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL:")
        print("   Ubuntu/Debian: sudo apt-get install openssl")
        print("   macOS: brew install openssl")
        print("   Windows: Download from https://www.openssl.org/")
        return False

if __name__ == "__main__":
    success = generate_ssl_certificates()
    sys.exit(0 if success else 1) 