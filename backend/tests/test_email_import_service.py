import logging
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.exceptions import EmbeddingGenerationError
from services.email_import_service import (
    EMBEDDING_DIMENSION,
    EmailImportEmbeddingProvider,
    _generate_import_embeddings,
    _import_single_eml,
    _safe_item_filename,
    _safe_upload_filename,
)


@pytest.mark.parametrize(
    "input_name,expected",
    [
        ("file.zip", "file.zip"),
        ("", "upload"),
        (None, "upload"),
        ("/some/path/file.zip", "file.zip"),
        ("  spaced.zip  ", "spaced.zip"),
        ("/", "upload"),
    ]
)
def test_safe_upload_filename(input_name, expected):
    assert _safe_upload_filename(input_name) == expected

@pytest.mark.parametrize(
    "upload_name,eml_path,expected",
    [
        # without eml_path
        ("my_archive.zip", None, "my_archive.zip"),
        ("", None, "upload"),
        ("/path/to/my_archive.zip", None, "my_archive.zip"),

        # matching eml_path
        ("my_file.eml", Path("my_file.eml"), "my_file.eml"),
        ("/path/my_file.eml", Path("/other/path/my_file.eml"), "my_file.eml"),
        ("  my_file.eml  ", Path("my_file.eml"), "my_file.eml"),

        # differing eml_path
        ("my_archive.zip", Path("email_1.eml"), "my_archive.zip:email_1.eml"),
        ("/path/my_archive.zip", Path("/some/folder/email_1.eml"), "my_archive.zip:email_1.eml"),
        ("", Path("email_1.eml"), "upload:email_1.eml"),
    ]
)
def test_safe_item_filename(upload_name, eml_path, expected):
    assert _safe_item_filename(upload_name, eml_path) == expected


@pytest.mark.asyncio
async def test_import_single_eml_rejects_symlink(tmp_path):
    target_path = tmp_path / "target.txt"
    target_path.write_text("not an eml")
    symlink_path = tmp_path / "message.eml"
    symlink_path.symlink_to(target_path)
    session = AsyncMock(spec=AsyncSession)

    result = await _import_single_eml(
        session,
        eml_path=symlink_path,
        display_filename="message.eml",
        user_id="user-1",
        organization_id="org-1",
    )

    assert result.status == "failed"
    assert result.reason_code == "parse_failed"
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_generate_import_embeddings_logs_non_secret_provider_fallback(caplog):
    provider = EmailImportEmbeddingProvider(
        api_key="secret-provider-token",
        base_url="http://ollama:11434/v1",
        embedding_model="embeddinggemma",
    )
    caplog.set_level(logging.WARNING, logger="services.email_import_service")

    with patch(
        "services.email_import_service.generate_embeddings",
        new_callable=AsyncMock,
    ) as mock_generate_embeddings:
        mock_generate_embeddings.side_effect = EmbeddingGenerationError(
            "secret-provider-token unavailable at http://ollama:11434/v1"
        )

        embeddings = await _generate_import_embeddings(
            ["Provider body"],
            embedding_provider=provider,
        )

    assert embeddings == [[0.0] * EMBEDDING_DIMENSION]
    assert "Email import embedding generation failed" in caplog.text
    assert "error_type=EmbeddingGenerationError" in caplog.text
    assert "text_count=1" in caplog.text
    assert "secret-provider-token" not in caplog.text
    assert "ollama" not in caplog.text
    assert "embeddinggemma" not in caplog.text


@pytest.mark.asyncio
async def test_generate_import_embeddings_recovers_valid_items_after_batch_failure():
    provider = EmailImportEmbeddingProvider(
        api_key="secret-provider-token",
        base_url="http://ollama:11434/v1",
        embedding_model="embeddinggemma",
    )

    with patch(
        "services.email_import_service.generate_embeddings",
        new_callable=AsyncMock,
    ) as mock_generate_embeddings:
        mock_generate_embeddings.side_effect = [
            EmbeddingGenerationError("batch failed"),
            [[0.25] * EMBEDDING_DIMENSION],
            EmbeddingGenerationError("single item failed"),
            [[0.75] * (EMBEDDING_DIMENSION // 2)],
        ]

        embeddings = await _generate_import_embeddings(
            ["body", "bad attachment", "good attachment"],
            embedding_provider=provider,
        )

    assert mock_generate_embeddings.await_count == 4
    assert mock_generate_embeddings.await_args_list[1].args[0] == ["body"]
    assert mock_generate_embeddings.await_args_list[2].args[0] == ["bad attachment"]
    assert mock_generate_embeddings.await_args_list[3].args[0] == ["good attachment"]
    assert embeddings[0] == [0.25] * EMBEDDING_DIMENSION
    assert embeddings[1] == [0.0] * EMBEDDING_DIMENSION
    assert embeddings[2] == [0.75] * (EMBEDDING_DIMENSION // 2) + [0.0] * (
        EMBEDDING_DIMENSION // 2
    )
