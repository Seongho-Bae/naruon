import re

with open("backend/api/dav.py", "r") as f:
    content = f.read()

content = content.replace("safe_path = _sanitize_log_value(repr(path)[1:-1])", "safe_path = _sanitize_log_value(repr(path)[1:-1])\n    # Note: repr already escapes newlines and control characters as \\n, \\r, \\x1b, etc.\n    # Using _sanitize_log_value on the result of repr is harmless but redundant for those.")
with open("backend/api/dav.py", "w") as f:
    f.write(content)
