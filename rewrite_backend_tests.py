# 3. Update backend tests
with open("backend/tests/test_llm_service.py", "r") as f:
    content = f.read()

if "test_translate_email_body_success" not in content:
    content = content.replace("from services.llm_service import (", "from services.llm_service import (\ntranslate_email_body,")
    test_code = """
@pytest.mark.asyncio
async def test_translate_email_body_success(mock_openai):
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "번역된 메일입니다."
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await translate_email_body(
        "This is an email.",
        "Korean",
        "test-key"
    )

    assert result == "번역된 메일입니다."
    mock_openai.chat.completions.create.assert_called_once()
    kwargs = mock_openai.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == settings.OPENAI_MODEL
    assert kwargs["temperature"] == 0.3

@pytest.mark.asyncio
async def test_translate_email_body_api_error(mock_openai):
    mock_openai.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

    with pytest.raises(LLMServiceError, match="LLM API error during translation"):
        await translate_email_body("Test email", "Korean", "test-key")

@pytest.mark.asyncio
async def test_translate_email_body_missing_api_key():
    with pytest.raises(ValueError, match="API Key is not set"):
        await translate_email_body("Test email", "Korean", "")

@pytest.mark.asyncio
async def test_translate_email_body_uses_selected_provider_model(mock_openai):
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Gemma translation"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await translate_email_body(
        "Test email",
        "Korean",
        "test-key",
        model="gemma4",
    )

    assert result == "Gemma translation"
    assert mock_openai.chat.completions.create.call_args.kwargs["model"] == "gemma4"
"""
    content += test_code
    with open("backend/tests/test_llm_service.py", "w") as f:
        f.write(content)

with open("backend/tests/test_llm_api.py", "r") as f:
    content = f.read()

if "test_translate_endpoint" not in content:
    test_code = """
@patch("api.llm.translate_email_body", new_callable=AsyncMock)
def test_translate_endpoint(mock_translate, client):
    mock_translate.return_value = "이것은 번역입니다."

    resp = client.post(
        "/api/llm/translate",
        json={"email_body": "test email", "target_language": "Korean"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"translation": "이것은 번역입니다."}
    forwarded_prompt, forwarded_language, forwarded_key = mock_translate.await_args.args[:3]
    assert forwarded_prompt == "test email"
    assert forwarded_language == "Korean"
    assert forwarded_key == "test-key"

@patch("api.llm.translate_email_body", new_callable=AsyncMock)
def test_translate_endpoint_uses_active_local_model_provider(mock_translate):
    provider = LLMProvider(
        id=7,
        user_id="admin",
        organization_id="org-acme",
        name="Local Gemma4",
        provider_type="ollama",
        base_url="http://ollama:11434/v1",
        model_identifier="gemma4",
        embedding_model="embeddinggemma",
        api_key=None,
        is_active=True,
    )
    mock_translate.return_value = "Gemma4 translation"

    async def override_get_db():
        yield MockSession(
            tenant_config=MockTenantConfig(openai_api_key=None),
            providers=[provider],
        )

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "testuser",
                "X-Organization-Id": "org-acme",
            },
        ) as test_client:
            resp = test_client.post(
                "/api/llm/translate",
                json={"email_body": "test email", "target_language": "Korean"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == {"translation": "Gemma4 translation"}
    forwarded_prompt, forwarded_language, forwarded_key = mock_translate.await_args.args[:3]
    assert forwarded_prompt == "test email"
    assert forwarded_language == "Korean"
    assert forwarded_key == LOCAL_PROVIDER_API_KEY
    assert mock_translate.await_args.kwargs == {
        "base_url": "http://ollama:11434/v1",
        "model": "gemma4",
    }

def test_translate_endpoint_rejects_unexpected_fields(client):
    translate = client.post(
        "/api/llm/translate",
        json={"email_body": "test email", "target_language": "Korean", "unexpected_field": "boom"},
    )
    assert translate.status_code == 422
    assert any(
        error["loc"][-1] == "unexpected_field" and error["type"] == "extra_forbidden"
        for error in translate.json()["detail"]
    )

def test_translate_endpoints_preserve_missing_key_400():
    async def override_get_db():
        yield MockSession(MockTenantConfig(openai_api_key=None))

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, headers={"X-User-Id": "testuser"}) as test_client:
            translate = test_client.post(
                "/api/llm/translate", json={"email_body": "test email", "target_language": "Korean"}
            )
    finally:
        app.dependency_overrides.clear()

    assert translate.status_code == 400
    assert translate.json() == {"detail": "OpenAI API key not configured"}

@patch("api.llm.translate_email_body", new_callable=AsyncMock)
def test_translate_api_error_returns_500(mock_translate, client):
    from core.exceptions import LLMServiceError
    mock_translate.side_effect = LLMServiceError("API Error")

    resp = client.post(
        "/api/llm/translate",
        json={"email_body": "test email", "target_language": "Korean"},
    )
    assert resp.status_code == 500
    assert resp.json() == {"detail": "An internal server error occurred while processing the request."}

@patch("api.llm.translate_email_body", new_callable=AsyncMock)
def test_translate_generic_error_returns_500(mock_translate, client):
    mock_translate.side_effect = Exception("Generic Error")

    resp = client.post(
        "/api/llm/translate",
        json={"email_body": "test email", "target_language": "Korean"},
    )
    assert resp.status_code == 500
    assert resp.json() == {"detail": "An internal server error occurred while processing the request."}

@patch("api.llm.translate_email_body", new_callable=AsyncMock)
def test_translate_wrong_user_returns_403(mock_translate, client):
    resp = client.post(
        "/api/llm/translate?user_id=wrong_user",
        json={"email_body": "test email", "target_language": "Korean"},
    )
    assert resp.status_code == 403
    assert resp.json() == {"detail": "Not authorized"}
"""
    content += test_code
    with open("backend/tests/test_llm_api.py", "w") as f:
        f.write(content)
