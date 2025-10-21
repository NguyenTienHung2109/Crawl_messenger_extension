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
cert.gmtime_adj_notAfter(365*24*60*60)
cert.set_issuer(cert.get_subject())
cert.set_pubkey(k)
cert.sign(k, 'sha256')

# Write to files
with open('cert.pem', 'wb') as f:
    f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
with open('key.pem', 'wb') as f:
    f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

print('SSL certificates created: cert.pem, key.pem')
