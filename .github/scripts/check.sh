#!/usr/bin/env bash

set -eu

black --check --diff .
isort --check --diff .
autoflake --recursive --check --quiet .
mypy pyuow
safety check

exit 0
