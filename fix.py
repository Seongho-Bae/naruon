with open("scripts/ci/test_strix_quick_gate.sh") as f:
    text = f.read()

import re

# Patch the setup logic
text = re.sub(
    r'elif \[ "\$scenario" = "multi-source-dirs-existing-endpoint" \]; then',
    r'elif [ "$scenario" = "multi-source-dirs-existing-endpoint" ] || [ "$scenario" = "multi-source-dirs-hallucinated-endpoint" ]; then',
    text
)

# Patch the test case
idx = text.find('run_gate_case "preserve-existing-api-base"')
if idx != -1:
    new_test = """run_gate_case "multi-source-dirs-hallucinated-endpoint" \\
	"vertex_ai/hallucination-primary" \\
	"vertex_ai/fallback-one vertex_ai/fallback-two" \\
	"0" \\
	"Strix quick scan succeeded with fallback model 'vertex_ai/fallback-one'." \\
	"2" \\
	"vertex_ai/hallucination-primary|vertex_ai/fallback-one" \\
	"<unset>|<unset>" \\
	"vertex_ai" \\
	"__DEFAULT__" \\
	"" \\
	"1" \\
	"CRITICAL" \\
	"0" \\
	"" \\
	"src api"

"""
    text = text[:idx] + new_test + text[idx:]
    with open("scripts/ci/test_strix_quick_gate.sh", "w") as f:
        f.write(text)
    print("Done")
else:
    print("Failed to find preserve-existing-api-base")
