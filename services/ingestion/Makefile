.PHONY: lint format type-check run-live run-backfill

lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy app/

run-live:
	functions-framework --target=ingest --port=8080 --source=app/live.py

run-backfill:
	python -m app.backfill
