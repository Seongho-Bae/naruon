<skill_content name="fix-development-mistakes">
# Skill: fix-development-mistakes

# Fix Development Mistakes

## Overview

A skill to fix linter errors, dependency downgrades, security vulnerabilities, file overwrites, and other mistakes that occur during development. This ensures root causes are traced and fixed properly without human intervention.

## When to use

Use this skill when:
- Dependabot or code scanning alerts report a vulnerability.
- A subagent overwrites a file instead of appending to it (e.g. `exceptions.py` or `requirements.txt`).
- A linter or static analyzer throws an error (e.g., `mypy`, `flake8`, `ruff`).
- Merge conflicts result in accidental loss of code or unintended dependency downgrades.

## Workflow

### 1. Root Cause Analysis
- **Identify the error:** Read the error message, warning, or security alert.
- **Trace back:** Check git logs or `git diff` to see what introduced the error.
- **Understand why:** Did a subagent misunderstand a prompt? Did a package conflict force a downgrade? Was a security patch reverted?

### 2. Formulate the Fix
- **File overwrites:** Use `git checkout origin/master -- <file>` to restore the original content, then append the new changes safely using the `edit` or `write` tool.
- **Dependency issues:** Pin dependencies to secure versions. Resolve conflicts by upgrading the conflicting package rather than downgrading the patched package.
- **Linter errors:** Add missing type hints, fix indentation, add docstrings, or suppress the warning ONLY if the rule is intentionally violated and commented.

### 3. Execution & Verification
- Execute the fix using appropriate tools (`edit`, `write`, `bash`).
- Run the test suite and the linter locally.
- Confirm the warning, error, or vulnerability is resolved.

### 4. Commit and Push
- Commit the change with a descriptive message starting with `fix: `.
- Example: `fix: restore exceptions.py overwritten by subagent` or `fix: upgrade pytest to 9.0.3 to resolve CVE-2025-71176`.
- Push directly if on a feature branch, or create a PR if on master.
</skill_content>