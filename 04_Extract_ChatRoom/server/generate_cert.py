#!/usr/bin/env python3
"""
Generate self-signed SSL certificate for development
"""

import subprocess
import sys
import os

def generate_with_openssl():
    """Try to generate using OpenSSL command"""
    try:
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
            '-out', 'cert.pem', '-keyout', 'key.pem', '-days', '365',
            '-subj', '/CN=ho-dev-ai'
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print('✅ SSL certificates generated using OpenSSL')
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def generate_with_python():
    """Generate using Python's ssl module"""
    try:
        from OpenSSL import crypto

        # Generate key
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)

        # Generate certificate
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().O = "Dev Server"
        cert.get_subject().CN = "ho-dev-ai"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for 1 year
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')

        # Write to files
        with open('cert.pem', 'wb') as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open('key.pem', 'wb') as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

        print('✅ SSL certificates generated using pyOpenSSL')
        return True
    except ImportError:
        return False

def generate_simple():
    """Generate using Python built-in ssl (Python 3.10+)"""
    try:
        import ssl
        import datetime

        # Create certificate
        ssl.create_default_context()

        # This is a simple approach - write basic cert
        cert_content = """-----BEGIN CERTIFICATE-----
MIICpDCCAYwCCQDU7WV7BJ8V8jANBgkqhkiG9w0BAQsFADAUMRIwEAYDVQQDDAlo
by1kZXYtYWkwHhcNMjQwMTAxMDAwMDAwWhcNMjUwMTAxMDAwMDAwWjAUMRIwEAYD
VQQDDAloby1kZXYtYWkwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDK
example_cert_data_here
-----END CERTIFICATE-----"""

        key_content = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAyexample_key_data_here
-----END RSA PRIVATE KEY-----"""

        print('⚠️  Using manual SSL generation. Better to install pyOpenSSL or OpenSSL')
        print('    Run: pip install pyOpenSSL')
        return False

    except Exception as e:
        return False

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if generate_with_openssl():
        sys.exit(0)
    elif generate_with_python():
        sys.exit(0)
    else:
        print('❌ Could not generate SSL certificates')
        print('Please install one of:')
        print('  1. OpenSSL: https://slproweb.com/products/Win32OpenSSL.html')
        print('  2. pyOpenSSL: pip install pyOpenSSL')
        sys.exit(1)
