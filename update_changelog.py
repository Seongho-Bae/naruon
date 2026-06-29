import datetime

with open("CHANGELOG.md", "r") as f:
    content = f.read()

today = datetime.datetime.now().strftime("%Y-%m-%d")
new_entry = """
### Added
- 백엔드에 다국어 이메일 본문을 번역할 수 있는 LLM 기반 `POST /api/llm/translate` 엔드포인트를 추가했습니다.
- 프론트엔드의 이메일 상세 정보 뷰(`EmailDetail.tsx`)에 메일 원문을 한국어로 번역하는 '번역' 액션 버튼 및 번역 결과 UI를 추가했습니다.

"""

if "## [Unreleased]" in content:
    parts = content.split("## [Unreleased]", 1)
    content = parts[0] + "## [Unreleased]\n" + new_entry + parts[1]
else:
    content = "## [Unreleased]\n" + new_entry + content

with open("CHANGELOG.md", "w") as f:
    f.write(content)
