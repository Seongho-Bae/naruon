source scripts/ci/strix_quick_gate.sh >/dev/null 2>&1 || true
is_github_models_model "openai/gpt-5.4" && echo "YES" || echo "NO"
