import pytest
from unittest.mock import patch, AsyncMock
from scripts.import_fixtures import process_zip_file


@pytest.mark.asyncio
async def test_process_zip_file():
    with patch("scripts.import_fixtures.extract_backup_async") as mock_extract:
        with patch("scripts.import_fixtures.parse_eml") as mock_parse:
            with patch("scripts.import_fixtures.generate_embeddings") as mock_embed:
                mock_extract.return_value = []
                # Ensure it doesn't crash on an empty zip
                await process_zip_file("dummy.zip", AsyncMock())
