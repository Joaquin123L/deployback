import secrets

def generate_token():
    return secrets.token_hex(32)  # Genera un token de 64 caracteres (32 bytes en hexadecimal)
