from db.models import LLMProvider

LOCAL_PROVIDER_TYPES = frozenset({"local", "ollama", "vllm", "openai-compatible-local"})


def _has_value(value: str | None) -> bool:
    return bool(value and value.strip())


def is_llm_provider_configured(provider: LLMProvider) -> bool:
    if _has_value(provider.api_key):
        return True

    provider_type = (provider.provider_type or "").strip().lower()
    if provider_type not in LOCAL_PROVIDER_TYPES:
        return False

    return _has_value(provider.base_url) and _has_value(provider.model_identifier)


def llm_provider_model_label(provider: LLMProvider) -> str:
    model_identifier = (provider.model_identifier or "").strip()
    return model_identifier or provider.provider_type
