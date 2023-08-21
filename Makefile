.PHONY: tests

tests:
	pytest --cov --cov-report term-missing
