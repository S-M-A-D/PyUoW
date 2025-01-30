# PyUoW Contribution Guide

Thank you for considering contributing to PyUow!
This guide will help you set up your development environment and provide guidelines for making contributions.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting Up Your Environment](#setting-up-your-environment)
3. [Running Tests](#running-tests)
4. [Using Pre-commit Hooks](#using-pre-commit-hooks)
5. [Project Layout](#project-layout)
6. [Submitting Contributions](#submitting-contributions)

## Getting Started

To get started with contributing, you'll need to set up your development environment.
We use `poetry` to manage dependencies, so it's important to have it installed globally.

## Setting Up Your Environment

### 1. Clone the Repository

Start by cloning the repository to your local machine:

```bash
git clone git@github.com:S-M-A-D/PyUoW.git
cd pyuow
```

Optionally, you can configure your GitHub username and email if you haven't already.
This is important for associating your commits with your GitHub account:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. Install Poetry

Poetry is a dependency manager that helps manage your project's packages.
Install it globally using the following command:

```bash
curl -sSL https://install.python-poetry.org | python -
```

Optionally, you can specify `POETRY_HOME` to install Poetry in a custom directory:

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | POETRY_HOME=`pwd`/.poetry python -
```

After installation, follow the on-screen instructions to add `poetry` to your `PATH`.

### 3. Install Dependencies

After installing Poetry, you can install the project dependencies into a virtual environment.

```bash
poetry env use python
poetry shell
poetry install
```

This will create a virtual environment and install all dependencies specified in the `pyproject.toml` file.

## Running Tests

To ensure that your contributions don't introduce any issues, run the project's test suite using the following command:

```bash
make tests
```

This command will execute all tests and report any failures.

## Formatting codebase

To ensure that your contributions follow the project's coding standards, format your code using the following command:

```bash
make fmt
```

## Using Pre-commit Hooks

We use `pre-commit` hooks to automatically check and format your code before you commit changes.
These hooks help maintain code quality and consistency.

### Enabling Pre-commit Hooks

To enable the pre-commit hooks, run this command once:

```bash
pre-commit install
```

Once installed, the hooks will automatically format and fix issues in the files staged for committing.

### Running Hooks Manually

You can also manually execute the pre-commit hooks at any time by running:

```bash
pre-commit run
```

## Project Layout

Understanding the project structure will help you navigate the codebase and contribute effectively.

```
pyuow
├── .github                             # GitHub plugins and CI jobs.
├── pyuow                               # Library sources.
├── static                              # Project specific resources, unrelated to the pip package.
└── tests                               # Tests package (structure is mirrored from src).
```

## Submitting Contributions

When you're ready to submit your changes, please ensure that:

1. All tests pass.
2. Code adheres to the style and guidelines enforced by the pre-commit hooks.
3. Your commit messages are clear and descriptive.

Submit your changes via a pull request. We'll review your changes and provide feedback if needed.
