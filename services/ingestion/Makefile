.PHONY: lint format type-check run

lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy app/

run:
	functions-framework --target=ingest --port=8080 --source=app/main.py
