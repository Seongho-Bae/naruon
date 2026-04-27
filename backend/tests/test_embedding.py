import pytest
from services.embedding import chunk_text

def test_chunk_text():
    text = "This is a long test string. " * 100
    chunks = chunk_text(text, chunk_size=50)
    assert len(chunks) > 1
    assert len(chunks[0]) <= 50
