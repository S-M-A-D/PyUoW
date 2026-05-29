.PHONY: fmt tests docs-serve

fmt:
	ruff check --fix .
	ruff format .
	mypy .

tests:
	pytest --cov --cov-report term-missing

docs-serve:
	mkdocs serve
