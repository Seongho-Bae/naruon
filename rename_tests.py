import os
import re

files_to_update = []
for root, dirs, files in os.walk('backend'):
    for file in files:
        if file.endswith('.py'):
            files_to_update.append(os.path.join(root, file))

replacements = {
    # If the property changed on model, we need to update usage
    '"emails"': '"email_items"',
    "'emails'": "'email_items'",
    '"organizations"': '"organization_entities"',
    "'organizations'": "'organization_entities'",
    '"attachments"': '"file_attachments"',
    "'attachments'": "'file_attachments'",
    '"workspaces"': '"workspace_entities"',
    "'workspaces'": "'workspace_entities'",
    '"users"': '"user_entities"',
    "'users'": "'user_entities'",
    '"accounts"': '"auth_accounts"',
    "'accounts'": "'auth_accounts'",
    '"documents"': '"document_entities"',
    "'documents'": "'document_entities'",
}

# we need to be careful with `.emails` on test fixtures
test_replacements = {
    ".emails": ".email_items",
    ".attachments": ".file_attachments",
    ".organizations": ".organization_entities",
    ".workspaces": ".workspace_entities",
    ".users": ".user_entities",
    ".accounts": ".auth_accounts",
    ".documents": ".document_entities",
}

for file_path in files_to_update:
    if not file_path.startswith('backend/tests/'): continue
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content
    for old, new in replacements.items():
        content = content.replace(old, new)

    for old, new in test_replacements.items():
        content = content.replace(old, new)

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)

print("Replacement complete for test files.")
