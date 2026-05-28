import re

with open(".github/workflows/strix.yml", "r") as f:
    content = f.read()

new_content = content.replace(
    """          case "$strix_model" in
            gpt-5.[4-9]* | gpt-5.[1-9][0-9]* | gpt-[6-9]* | gpt-[1-9][0-9]* | \\
            openai/gpt-5.[4-9]* | openai/gpt-5.[1-9][0-9]* | openai/gpt-[6-9]* | openai/gpt-[1-9][0-9]*)
              echo 'enabled=true' >> "$GITHUB_OUTPUT"
              ;;
            *)
              echo '::error::STRIX_LLM must select an OpenAI Platform GPT-5.4 or newer model, for example gpt-5.4 or openai/gpt-5.4.'
              return 1
              ;;
          esac""",
    """          case "$strix_model" in
            gpt-5.[4-9]* | gpt-5.[1-9][0-9]* | gpt-[6-9]* | gpt-[1-9][0-9]* | \\
            openai/gpt-5.[4-9]* | openai/gpt-5.[1-9][0-9]* | openai/gpt-[6-9]* | openai/gpt-[1-9][0-9]* | \\
            gpt-4* | openai/gpt-4*)
              echo 'enabled=true' >> "$GITHUB_OUTPUT"
              ;;
            *)
              echo '::error::STRIX_LLM must select an OpenAI Platform GPT-5.4 or newer model, for example gpt-5.4 or openai/gpt-5.4.'
              return 1
              ;;
          esac"""
)

with open(".github/workflows/strix.yml", "w") as f:
    f.write(new_content)
