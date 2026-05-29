# Contributing

Thanks for considering a contribution to PyUoW! This page covers the dev setup. The canonical [CONTRIBUTING.md](https://github.com/S-M-A-D/PyUoW/blob/main/CONTRIBUTING.md) in the repo is the source of truth.

## Setup

```bash
git clone git@github.com:S-M-A-D/PyUoW.git
cd PyUoW

# Poetry-managed dev environment
poetry env use python
poetry install --with docs

# Pre-commit hooks
pre-commit install
```

## Common tasks

```bash
make tests        # pytest with coverage
make fmt          # ruff check --fix + ruff format + mypy
make docs-serve   # mkdocs serve - live preview at http://127.0.0.1:8000
```

## Adding a feature

1. Open an issue first if the change is non-trivial.
2. Add a unit test mirroring the existing structure under `tests/`.
3. Run `make fmt` and `make tests` locally.
4. Open a PR — CI will run ruff, mypy, the full test matrix across Python 3.10–3.14, and pip-audit.

## Code style

- `ruff format` enforces formatting (line length 79).
- `ruff check` enforces import order and unused-import/variable rules.
- `mypy --strict` is enforced — no `Any` leaks, no implicit re-exports.
- Tests follow BDD-style `# given / # when / # then` comments.

## Project layout

```text
pyuow/                # library sources
├── context/          # context base classes + datapoint contexts
├── datapoint/        # datapoint spec / producer / consumer
├── domain/           # Model, Batch, ChangeType, events, exceptions
├── entity/           # Entity, AuditedEntity, SoftDeletable, Versioned, Version
├── repository/       # repository ABCs + DomainRepository
├── result/           # Result + MissingOutError
├── unit/             # BaseUnit, FlowUnit, ConditionalUnit, RunUnit, FinalUnit, ErrorUnit
├── work/             # work managers (noop, transactional, transactional.domain)
├── contrib/
│   └── sqlalchemy/   # SQLAlchemy integration
└── aio/              # top-level async re-exports

tests/                # mirrors pyuow/ layout
docs/                 # mkdocs sources
```

Every concept has an `aio/` sibling where applicable — see [Async support](async.md).
