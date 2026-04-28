import base64
import pytest
from services.email_client import generate_oauth2_string


def test_generate_oauth2_string():
    result = generate_oauth2_string("test@example.com", "dummy_token")
    decoded = base64.b64decode(result)
    assert b"user=test@example.com" in decoded
    assert b"auth=Bearer dummy_token" in decoded
