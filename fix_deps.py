with open("requirements-strix-ci.txt", "r") as f:
    content = f.read()
# We don't need to change requirements-strix-ci.txt because it's just the top level. The issue is in requirements-strix-ci-hashes.txt.
# Let's see what pip-compile output.
