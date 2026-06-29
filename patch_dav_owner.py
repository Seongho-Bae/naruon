import re

with open("backend/api/dav.py", "r") as f:
    content = f.read()

# Add unquote import
if "from urllib.parse import unquote" not in content:
    content = content.replace("from html import escape as escape_xml_text\n\nfrom fastapi", "from html import escape as escape_xml_text\nfrom urllib.parse import unquote\n\nfrom fastapi")

content = content.replace('def _dav_path_owner_user_id(path: str) -> str | None:\n    if ".." in path.split("/"):\n        return None', 'def _dav_path_owner_user_id(path: str) -> str | None:\n    path = unquote(path)\n    if ".." in path.split("/"):\n        return None')

with open("backend/api/dav.py", "w") as f:
    f.write(content)
