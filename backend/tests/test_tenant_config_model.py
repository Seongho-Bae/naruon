import pytest
from db.models import TenantConfig

def test_tenant_config_model_exists():
    config = TenantConfig(user_id="test_user", openai_api_key="test_key")
    assert config.user_id == "test_user"
    assert config.openai_api_key == "test_key"
