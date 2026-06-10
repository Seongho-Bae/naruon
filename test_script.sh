source scripts/ci/strix_model_utils.sh

is_github_models_model() {
	case "$1" in
	openai/openai/* | github_models/* | \
	deepseek/* | meta/* | mistral-ai/*)
		return 0
		;;
	*)
		return 1
		;;
	esac
}
echo "For openai/gpt-5.4:"
is_github_models_model "openai/gpt-5.4" && echo "YES" || echo "NO"
