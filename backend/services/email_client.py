import base64

def generate_oauth2_string(user: str, access_token: str) -> bytes:
    """Generates an OAuth2 string for IMAP/SMTP authentication."""
    auth_string = f"user={user}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode("utf-8"))
