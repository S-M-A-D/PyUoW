.PHONY: fmt tests

fmt:
	ruff check --fix .
	ruff format .
	mypy .

tests:
	pytest --cov --cov-report term-missing
