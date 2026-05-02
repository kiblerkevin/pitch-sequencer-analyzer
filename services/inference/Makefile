.PHONY: lint format type-check run

lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy app/

run:
	uvicorn app.main:app --reload --port 8000
