# CLI reference

PyUoW ships a small CLI via the `pyuow` console script. It is included automatically when you `pip install pyuow`.

## Overview

```bash
pyuow --version        # show version
pyuow --help           # top-level help
pyuow install-skill --help   # subcommand help
```

You can also run the CLI as `python -m pyuow_cli`.

## Install

```bash
pip install pyuow
```

The script is registered as `pyuow`. No extra dependencies are required.

## `install-skill`

Drop an AI-agent skill file into a project or your user profile so Claude Code / OpenCode learn PyUoW's idioms.

### Flags

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--target` | `claude`, `opencode`, `both` | *(see below)* | Which agent to install for |
| `--global` | flag | off | Install into your home directory instead of the current project |
| `--check` | flag | off | Dry-run: report what would change without writing |
| `--force` | flag | off | Skip the interactive prompt and default to `both` |

**Target default:**

- On a TTY with no `--target` and no `--force`: an interactive prompt asks you to pick Claude, OpenCode, or both.
- In a non-TTY environment (CI, pipe): defaults to `both`.
- With `--force`: also defaults to `both`.

### Examples

Install for both agents in the current project:

```bash
pyuow install-skill
```

Install for a single agent:

```bash
pyuow install-skill --target claude
pyuow install-skill --target opencode
```

Install into your user profile (global):

```bash
pyuow install-skill --global
```

Dry-run to see what would change:

```bash
pyuow install-skill --check
```

Skip the prompt in an interactive shell:

```bash
pyuow install-skill --force
```

### What the command writes

The skill files are copied from the wheel at runtime. They contain frontmatter, a version stamp, and a curated reference of PyUoW idioms. See the [step-by-step guide](install-skill.md) for path details.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success (or `--check` found no differences) |
| `1` | Error: target path is a directory, permission denied, or `--check` found a difference |
| `130` | Interrupted by `Ctrl-C` (`KeyboardInterrupt`) |

Invalid arguments or unknown subcommands also return non-zero; argparse prints the error to stderr.

## Paths

The exact destination depends on `--global` and `--target`.

| Scope | Target | Path |
|-------|--------|------|
| Project | Claude | `.claude/skills/pyuow/SKILL.md` |
| Project | OpenCode | `.opencode/skills/pyuow.md` |
| Global | Claude | `~/.claude/skills/pyuow/SKILL.md` |
| Global | OpenCode | `~/.config/opencode/skills/pyuow.md` |

When the destination is a symlink, the command follows it and writes through to the resolved file. Broken symlinks are treated as missing files and recreated.

## FAQ

**Does the CLI require Click, Typer, or Rich?**

No. The CLI uses only the Python standard library (`argparse`).

**Can I install for Cursor or Copilot?**

No. Only Claude Code and OpenCode are supported.

**Is there an `uninstall-skill` subcommand?**

No. Remove the files manually if needed. The paths are listed above.

**What happens if the file already exists?**

The command compares content. If identical, it prints `up to date` and does nothing. If different, it overwrites silently.

**Does `--check` write anything?**

No. It only prints `would write` or `up to date` and returns `1` if a difference exists.

## See also

- [AI-agent skill](install-skill.md) — step-by-step user guide
- `pyuow install-skill --help`
