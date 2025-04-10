# Medical NER & Linking Service

This service provides named entity recognition (NER) and entity linking for biomedical text using spaCy with a scispaCy model. It exposes a REST API built with FastAPI to process text and return entities along with their medical details.

## Overview

- **Input:** JSON payload with a text field.
- **Processing:** Loads the `en_ner_bc5cdr_md` scispaCy model and attaches the linker during startup. When a request is received, the model extracts entities and looks up additional details.
- **Output:** JSON response listing the entities with linking details (e.g., CUI, score, canonical name, and aliases).

## Architecture

- **FastAPI:** Provides the REST API endpoints.
- **spaCy & scispaCy:** Performs NER and linking. [ScispaCy Repo](https://github.com/allenai/scispacy)
- **RxNorm:** Linking pipeline which contains ~100k concepts focused on normalized names for clinical drugs. [RxNorm website](https://www.nlm.nih.gov/research/umls/rxnorm/index.html)
- **Health Check Endpoint:** A dedicated `/health` endpoint is provided to verify the application's readiness.

## Features

- **/health Endpoint:** Returns a simple JSON indicating the service status.
- **/extract_entities Endpoint:** Accepts a JSON payload with a text field, performs NER and linking, and returns the extracted entities with additional details.

---

## Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t ner-service .
   ```

2. Run the container:
   ```bash
   docker run -d -p 8000:8000 ner-service
   ```

3. Test the service:
   ```bash
   curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"text": "This text contains ibuprofen and paracetamol"}' \
     http://localhost:8000/extract_entities
   ```

---

## Usage

### Example: Python Client

```python
import requests

api_url = "http://localhost:8000/extract_entities"
text = "The patient took ibuprofen."

response = requests.post(api_url, json={"text": text})
if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.status_code}")
```

---

## API response example

```json
{
  "entities": [
    {
      "text": "ibuprofen",
      "umls_entities": [
        {
          "canonical_name": "ibuprofen",
          "definition": "A non-steroidal anti-inflammatory agent with analgesic, antipyretic, and anti-inflammatory properties",
          "aliases": []
        }
      ]
    }
  ]
}
```

---

## Model Notes

The application uses the `en_ner_bc5cdr_md` model from [Scispacy](https://github.com/allenai/scispacy) along with the [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/index.html) linker. Make sure that any required model data is accessible at runtime. If not available locally, the model package can be installed via pip (refer to scispaCy's documentation for details).

---

## Configuration

The service can be configured using environment variables:

### Environment Variables

- `SPACY_MODEL`: SpaCy model to use (default: `en_ner_bc5cdr_md`)
- `LINKER_NAME`: Entity linker to use (default: `rxnorm`)

### Available Linkers

The following entity linkers are available through the `LINKER_NAME` configuration:

- **UMLS**: (~3M concepts) Links to Unified Medical Language System, levels 0, 1, 2, and 9
  - Note: The UMLS linker requires significant RAM (~10GB) to operate.
- **MeSH**: (~30K entities) Medical Subject Headings used for PubMed indexing
  - Note: Uses different identifiers than other KBs
- **RxNorm**: (~100K concepts) Clinical drugs ontology with normalized names
  - Includes: First Databank, Micromedex, Gold Standard Drug Database
- **GO**: (~67K concepts) Gene Ontology for biological functions of genes
- **HPO**: (~16K concepts) Human Phenotype Ontology for phenotypic abnormalities

---

## Development

### Setup

```bash
# Install the package in development mode
pip install -e ".[dev]"

# Download the required spaCy model
python -m spacy download en_ner_bc5cdr_md

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
pytest

# Run fast tests only (skipping slow model loading tests)
pytest -k "not test_nlp_model_loading and not test_nlp_entity_recognition and not test_nlp_abbreviation_detection"
```

### Linting

```bash
# Run all linters
./scripts/lint.sh
```

---

## Future Enhancements

- Make it possible to utilize full model pipeline (UMLS requires 10GB RAM to operate)
- Add support for **brand/trademark recognition**.
- Improve UMLS concept linking for ambiguous entities.
- Integrate additional NER models for multilingual support.

## Integration with PillChecker

This service is designed to be used as a component of the PillChecker application. When integrated as a submodule, it provides medical named entity recognition capabilities to the main application.

### Setup as a Submodule

1. Add as a submodule to the main PillChecker repository:
   ```bash
   git submodule add https://github.com/yourusername/PillChecker-model.git model
   ```

2. Install dependencies:
   ```bash
   cd model
   pip install -e ".[dev]"
   python -m spacy download en_ner_bc5cdr_md
   ```

3. Required environment variables:
   - `SPACY_MODEL`: SpaCy model to use (default: `en_ner_bc5cdr_md`)
   - `LINKER_NAME`: Entity linker to use (default: `rxnorm`)
   - See `.env.example` for all options

### API Usage from Parent Project

The main application should communicate with this service via HTTP:

```python
import requests

def extract_medical_entities(text):
    response = requests.post(
        "http://model:8081/api/extract_entities",
        json={"text": text}
    )
    return response.json()
```

### Testing

Run tests from the model directory:
```bash
# Run all tests
pytest

# Run fast tests only
pytest -k "not test_nlp_model_loading and not test_nlp_entity_recognition and not test_nlp_abbreviation_detection"
```
