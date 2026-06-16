with open(".jules/bolt.md", "r") as f:
    content = f.read()

fixed = content.replace("<<<<<<< HEAD\n", "").replace("=======\n", "").replace(">>>>>>> origin/develop\n", "")

with open(".jules/bolt.md", "w") as f:
    f.write(fixed)
