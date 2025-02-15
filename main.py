from typing import Any, Dict, List

import spacy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scispacy.abbreviation import AbbreviationDetector  # noqa: F401
from scispacy.linking import EntityLinker  # noqa: F401


def setup_model():
    """
    - **UMLS**: Links to the Unified Medical Language System, levels 0, 1, 2, and 9.
      This has approximately 3 million concepts.
    - **MeSH**: Links to the Medical Subject Headings. This contains a smaller set of higher-quality entities,
      which are used for indexing in PubMed. MeSH contains ~30k entities.
      **Note**: The MeSH knowledge base (KB) is derived directly from MeSH itself and, as such, uses different
      unique identifiers than the other KBs.
    - **RxNorm**: Links to the RxNorm ontology. RxNorm contains ~100k concepts focused on normalized names
      for clinical drugs. It includes several other drug vocabularies commonly used in pharmacy management
      and drug interaction, such as First Databank, Micromedex, and the Gold Standard Drug Database.
    - **GO**: Links to the Gene Ontology. The Gene Ontology contains ~67k concepts focused on the biological
      functions of genes.
    - **HPO**: Links to the Human Phenotype Ontology. The Human Phenotype Ontology contains ~16k concepts
      focused on phenotypic abnormalities encountered in human diseases.
    """

    print("Loading model...")
    model = spacy.load("en_ner_bc5cdr_md")
    model.add_pipe("abbreviation_detector")
    model.add_pipe(
        "scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "rxnorm"}
    )

    print("Model loaded!")
    return model


app = FastAPI()
root_nlp = setup_model()


class TextRequest(BaseModel):
    text: str


@app.post("/extract_entities", response_model=Dict[str, List[Dict[str, Any]]])
def extract_entities(req: TextRequest) -> Dict[str, List[Dict[str, Any]]]:
    """
    Process the input text and return recognized entities along with their UMLS details.
    """
    doc = root_nlp(req.text)
    entities = []

    # Retrieve the linker component to access UMLS mapping.
    linker = root_nlp.get_pipe("scispacy_linker")

    for ent in doc.ents:
        umls_entities = []
        for umls_ent in ent._.kb_ents:
            entity_detail = linker.kb.cui_to_entity[umls_ent[0]]
            print(entity_detail)
            if entity_detail:
                umls_entities.append(
                    {
                        # "cui": entity_detail.concept_id,
                        "canonical_name": entity_detail.canonical_name,
                        "definition": entity_detail.definition,
                        "aliases": entity_detail.aliases,
                    }
                )

        entities.append(
            {
                "text": ent.text,
                # "label": ent.label_,
                "umls_entities": umls_entities,
            }
        )

    return {"entities": entities}


@app.get("/health")
def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify that the application is running and the model is loaded.
    If the model is accessible, returns a simple JSON status.
    """
    if root_nlp is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    return {"status": "ok", "message": "Service is healthy"}
