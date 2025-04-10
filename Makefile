.PHONY: setup lint test test-fast docker-build docker-run

setup:
	pip install -e ".[dev]"
	python -m spacy download en_ner_bc5cdr_md
	pre-commit install

test-fast:
	pytest tests -v -k "not test_nlp_model_loading and not test_nlp_entity_recognition and not test_nlp_abbreviation_detection"

test:
	pytest tests -v

lint:
	./scripts/lint.sh

docker-build:
	docker build -t medical-ner-service .

docker-run:
	docker run -p 8081:8081 --env-file .env --rm medical-ner-service
