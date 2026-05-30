import sys

with open("scripts/ci/test_strix_quick_gate.sh", "r") as f:
    text = f.read()

text = text.replace('elif [ "$scenario" = "multi-source-dirs-existing-endpoint" ]; then', 'elif [ "$scenario" = "multi-source-dirs-existing-endpoint" ] || [ "$scenario" = "multi-source-dirs-hallucinated-endpoint" ]; then')

existing_case = """run_gate_case "multi-source-dirs-existing-endpoint" \\
	"vertex_ai/multi-dir-primary" \\
	"vertex_ai/fallback-one vertex_ai/fallback-two" \\
	"1" \\
	"Strix quick scan failed with a non-recoverable error." \\
	"1" \\
	"vertex_ai/multi-dir-primary" \\
	"<unset>" \\
	"vertex_ai" \\
	"__DEFAULT__" \\
	"" \\
	"0" \\
	"CRITICAL" \\
	"0" \\
	"" \\
	"src api"
"""

new_case = """
# Bug 2 follow-up: multi-entry STRIX_SOURCE_DIRS test for hallucinated endpoint.
# Endpoint /api/ghost-admin does not exist in src/ or api/.
# The gate must treat the finding as hallucinated -> fallback (exit 0).
run_gate_case "multi-source-dirs-hallucinated-endpoint" \\
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

if "multi-source-dirs-hallucinated-endpoint" not in text:
    text = text.replace(existing_case, existing_case + new_case)
    with open("scripts/ci/test_strix_quick_gate.sh", "w") as f:
        f.write(text)
    print("Patched.")
else:
    print("Already patched.")
