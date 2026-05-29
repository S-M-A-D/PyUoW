# AI Agent Skill

PyUoW ships with a **Claude Code / opencode skill** — a structured reference that tells AI coding agents how to use the library correctly. When the skill is installed, agents working in your project will recognise pyuow imports and produce idiomatic code instead of hallucinating a generic `UnitOfWork` class.

The skill is bundled inside the `pyuow` package itself, so no extra `pip install` is needed. You enable it with a one-liner per project (or globally).

## Quick start

```bash
pip install pyuow
pyuow install-skill
```

That's it. The default creates `./.claude/skills/pyuow/` as a symlink to the installed package's skill files, so `pip install -U pyuow` keeps the skill in sync automatically.

## Install scopes

```bash
pyuow install-skill              # ./.claude/skills/pyuow (default)
pyuow install-skill --global     # ~/.claude/skills/pyuow (all your projects)
pyuow install-skill --codex      # ~/.agents/skills/pyuow (Codex / codex-cli)
pyuow install-skill --path PATH  # PATH/pyuow (custom location)
```

All scopes are mutually exclusive. Pick the one that matches where your agent looks for skills.

## What the skill teaches

The bundled content is split across three files:

| File              | Purpose                                                              |
| ----------------- | -------------------------------------------------------------------- |
| `SKILL.md`        | Mental model, canonical sync example, sync-vs-async map, common mistakes table with concrete fixes for every sentinel exception (`FlowNotTerminatedError`, `FinalUnitError`, `CannotReassignUnitError`, `MissingOutError`, etc.). |
| `patterns.md`     | Six runnable recipes — sync flow, async flow, sync + SQLAlchemy transaction, async + SQLAlchemy transaction, repository pattern, domain batch handling. |
| `api-reference.md`| Full public export inventory organised by namespace, plus a key-signatures cheat sheet. |

The skill is intentionally tight: it leads with the parts that AI agents get wrong on first try (hallucinated `UnitOfWork`, `from pyuow.sqlalchemy import ...`, mixed sync/async namespaces, missing `.build()`).

## Symlink vs copy

By default the installer creates a **symlink** from the skill directory to the installed `pyuow/_skill/` inside your venv. Upside: `pip install -U pyuow` automatically picks up skill content updates.

If symlinks are not supported (Windows without Developer Mode, exotic filesystems), the installer falls back to copying. To force a copy explicitly:

```bash
pyuow install-skill --copy
```

After a copy install, re-run with `--force` after every `pip install -U pyuow` to refresh the content:

```bash
pyuow install-skill --force
```

`--force` works for both symlink and copy modes and overwrites the existing target.

## Verifying the install

```bash
$ pyuow install-skill
Installed pyuow skill -> /your/project/.claude/skills/pyuow (symlink)

$ cat .claude/skills/pyuow/SKILL.md | head -5
---
name: pyuow
description: Use when writing Python code that uses the pyuow library — ...
```

Open a fresh agent session in the project. When you ask it to write pyuow code, it should load the skill automatically (matched via the frontmatter `description`) and produce code that uses `BaseUnit` chains, the `>>` operator, `.build()`, and a `WorkManager`.

## Uninstalling

The skill is a single directory. Remove it like any other file:

```bash
rm -rf .claude/skills/pyuow                    # project-local
rm -rf ~/.claude/skills/pyuow                  # global
rm -rf ~/.agents/skills/pyuow                  # codex
```

The `pyuow` package itself is untouched.
