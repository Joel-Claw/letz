"""Tests for letz LOD client."""

import pytest
from unittest.mock import patch, MagicMock
from letz.lod import LODClient


@pytest.fixture
def client():
    with LODClient() as c:
        yield c


class TestLODClientInit:
    def test_default_config(self, client):
        assert client.cache_ttl == 86400 * 7
        assert client.timeout == 30.0

    def test_offline_mode(self):
        client = LODClient()
        assert client.timeout == 30.0


class TestCaching:
    def test_cache_path(self, client):
        path = client._get_cache_path("/api/v1/search", "Haus")
        assert "search" in str(path).lower() or "api" in str(path).lower()
        assert path.suffix == ".json"

    def test_cache_miss(self, client, tmp_path):
        client.cache_dir = tmp_path
        result = client._load_cache("/api/v1/search", "nonexistent")
        assert result is None


class TestCheckSpelling:
    @patch.object(LODClient, '_request')
    def test_word_found(self, mock_request):
        mock_request.return_value = [{"word": "Haus", "lemma": "Haus"}]
        client = LODClient()
        result = client.check_spelling("Haus")
        assert result["found"] is True

    @patch.object(LODClient, '_request')
    def test_word_not_found(self, mock_request):
        mock_request.return_value = []
        client = LODClient()
        result = client.check_spelling("xyzabc")
        assert result["found"] is False

    @patch.object(LODClient, '_request')
    def test_suggestions(self, mock_request):
        mock_request.return_value = [
            {"word": "Haus"},
            {"word": "Hauskapell"},
            {"word": "Haushälter"},
        ]
        client = LODClient()
        result = client.check_spelling("Hauz")
        assert len(result["suggestions"]) >= 1