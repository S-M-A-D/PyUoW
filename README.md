# PyUoW

***

###### [Python 3.11]


### Install requirements

This project is managed with `poetry`. All python dependencies have to be specified inside `pyproject.toml` file. Don't use `pip` directly, as the installed dependencies will be overridden by poetry during next `poetry install` run.

1. Install poetry globally:
    ```bash
    curl -sSL https://install.python-poetry.org | python -
    ```
   Optionally you can specify `POETRY_HOME` to install poetry to a custom directory:
    ```bash
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | POETRY_HOME=`pwd`/.poetry python -
    ```
   Follow the steps in the command's output to add `poetry` to `PATH`.

2. Install dependencies to virtualenv:
    ```bash
    poetry env use python
    poetry shell
    poetry install
    ```

### Commands

#### Run tests
```bash
make tests
```

### Pre-commit hooks
The repo contains configuration for `pre-commit` hooks that are run automatically before `git commit`
command. Inspect `.pre-commit-config.yaml` to learn which hooks are installed.

#### To enable hooks, just type once:
```bash
pre-commit install
```

Then changes staged for committing will be automatically fixed and styled.

#### To execute manually, run at any time:
```bash
pre-commit run
```

### CLI

The repo contains CLI tools. Run `server-cli --help` to learn which command are available.

:warning: CLI requires ENV variables to be set. If you are using ZSH, **dotenv** plugin will do it for you.

### Project Layout
```

pyuow
├── pyuow                               # library sources
└── tests                               # tests package (structure is mirrored from src)
```