.PHONY: fmt tests

fmt:
	isort .
	black .
	autoflake --recursive .
	mypy .

tests:
	pytest --cov --cov-report term-missing
