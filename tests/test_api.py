from unittest.mock import patch

import pytest
from fastapi import HTTPException
from medical_ner.main import app
from medical_ner.services.nlp import get_nlp_model


def test_health_endpoint(client):
    """Test the health endpoint returns 200 OK"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model is loaded" in data["message"]


def test_extract_entities(client):
    """Test entity extraction with mock data"""
    response = client.post("/api/extract_entities", json={"text": "Test text"})
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data

    # There should be at least one entity in the response
    # based on our mock implementation in conftest.py
    assert len(data["entities"]) > 0

    # Check the first entity matches our expected mock response
    entity = data["entities"][0]
    assert entity["text"] == "Test text"

    # Check that umls_entities exists and has the right structure
    assert "umls_entities" in entity
    if len(entity["umls_entities"]) > 0:
        umls_entity = entity["umls_entities"][0]
        assert "canonical_name" in umls_entity
        assert "definition" in umls_entity
        assert "aliases" in umls_entity


def test_extract_entities_error_handling(client):
    """Test error handling during entity extraction"""
    with patch(
        "medical_ner.services.linker.EntityLinker.extract_entities",
        side_effect=Exception("Test exception"),
    ):
        response = client.post("/api/extract_entities", json={"text": "Test text"})
        assert response.status_code == 500
        assert "Error processing text" in response.json()["detail"]


def test_extract_entities_empty_text(client):
    """Test handling of empty text input"""
    response = client.post("/api/extract_entities", json={"text": ""})
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    # With empty text, we expect no entities or just what the mock returns
    # which could be empty or a single entity based on implementation


def test_health_check_failure():
    """Test health check when model fails to load"""
    from medical_ner.api.router import health_check

    # Direct patch of the function call is fine for this case
    # because we're calling the function directly, not through FastAPI
    with patch(
            "medical_ner.api.router.get_nlp_model",
            side_effect=Exception("Model failed to load"),
    ):
        # Should raise an HTTP exception with 503 status code
        with pytest.raises(HTTPException) as excinfo:
            health_check()

        assert excinfo.value.status_code == 503
        assert "Model not properly loaded" in str(excinfo.value.detail)