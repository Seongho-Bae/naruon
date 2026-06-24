from typing import Any

def _dispatch_error(error_code: str) -> dict[str, Any]:
    return {
        "status": "error",
        "error": error_code,
        "error_code": error_code,
        "provider_write_executed": False,
    }
