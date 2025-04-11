import pytest
from fastapi.testclient import TestClient
from medical_ner.main import app
from medical_ner.services.nlp import get_nlp_model


# Dummy NLP model for testing
class DummyNLP:
    def __call__(self, text):
        return DummyDoc(text)

    def get_pipe(self, name):
        if name == "scispacy_linker":
            return DummyLinker()
        raise KeyError(f"Pipeline component {name} not found")

    # Add pipe_names property to match spaCy model API
    @property
    def pipe_names(self):
        return ["ner", "scispacy_linker"]


class DummyDoc:
    def __init__(self, text):
        self.text = text
        self.ents = [DummyEntity(text)]
        # Add _ attribute to the doc for abbreviations
        self._ = DummyDocExtensions()


class DummyDocExtensions:
    @property
    def abbreviations(self):
        return []  # Empty list of abbreviations


class DummyEntity:
    def __init__(self, text):
        self.text = text
        self._ = DummyEntityAttributes()


class DummyEntityAttributes:
    @property
    def kb_ents(self):
        return [("C0000001", 0.95)]

    @property
    def long_form(self):
        # Mock for abbreviation extension
        dummy = type("DummyLongForm", (), {"text": "chronic obstructive pulmonary disease"})
        return dummy


class DummyLinker:
    @property
    def kb(self):
        return DummyKB()


class DummyKB:
    @property
    def cui_to_entity(self):
        return {"C0000001": DummyEntityDetail()}


class DummyEntityDetail:
    @property
    def canonical_name(self):
        return "Test Entity"

    @property
    def definition(self):
        return "A test entity for unit testing."

    @property
    def aliases(self):
        return ["Test Alias 1", "Test Alias 2"]


@pytest.fixture
def client():
    """Create a test client with mocked NLP model"""
    # Create an instance of our dummy model
    dummy_nlp = DummyNLP()

    # Override the dependency in the app
    app.dependency_overrides[get_nlp_model] = lambda: dummy_nlp

    # Create test client
    test_client = TestClient(app)

    # Yield the client for tests to use
    yield test_client

    # Clean up after tests
    app.dependency_overrides.clear()