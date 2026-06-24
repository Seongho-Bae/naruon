import urllib.request
import os

token = os.environ.get("GITHUB_TOKEN")
if token:
    req = urllib.request.Request(
        "https://api.github.com/repos/ContextualWisdomLab/naruon/pulls/709/reviews",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req) as response:
        print(response.read().decode('utf-8'))
