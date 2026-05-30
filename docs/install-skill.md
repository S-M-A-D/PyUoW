# AI-agent skill

Drop a curated skill file into your project (or your user profile) so Claude Code and OpenCode understand PyUoW idioms while you work.

## Why install a skill

AI agents work best when they know the library you are using. The PyUoW skill file is a compact reference of units, flows, Result, Work Managers, and common pitfalls. It is version-locked to the release you have installed, so the agent's advice matches the code on disk.

## Prerequisites

- Python ≥ 3.10
- PyUoW installed: `pip install pyuow`
- Claude Code or OpenCode available in your environment

## Install in a project

Run the command inside any project that uses PyUoW:

```bash
pyuow install-skill
```

If your terminal is interactive, a short prompt asks which agent to target:

```
Select targets:
  1) Claude
  2) OpenCode
  3) Both
Press Enter for both:
```

Press Enter (or choose 3) to install for both. The files land at:

- `.claude/skills/pyuow/SKILL.md`
- `.opencode/skills/pyuow.md`

These paths are already ignored by the `.gitignore` rules PyUoW ships, so they will not clutter your repository.

## Install for your user account

To make the skill available in every project without reinstalling, use `--global`:

```bash
pyuow install-skill --global
```

Global paths are:

- Claude: `~/.claude/skills/pyuow/SKILL.md`
- OpenCode: `~/.config/opencode/skills/pyuow.md`

Project-level files take precedence over global ones in both ecosystems, so you can still override per-repository if needed.

## Pick a single target

If you only use one agent, skip the prompt by passing `--target`:

```bash
pyuow install-skill --target claude
pyuow install-skill --target opencode
```

Both commands write only the file for that agent.

## Verify it worked

Check that the file exists and contains the expected frontmatter:

```bash
cat .claude/skills/pyuow/SKILL.md
```

You should see YAML frontmatter at the top:

```yaml
---
name: pyuow
description: Use this skill whenever working with the PyUoW library ...
---
```

Below the frontmatter, look for a version stamp such as `<!-- Generated for pyuow 0.9.1 -->`. That stamp confirms the skill matches your installed PyUoW version.

## Updating after a PyUoW upgrade

After upgrading PyUoW, reinstall the skill to pick up any new idioms or corrected examples:

```bash
pip install -U pyuow
pyuow install-skill
```

To preview changes before writing, use `--check`:

```bash
pyuow install-skill --check
```

This prints `up to date` if the skill is already current, or `would write` if an update is pending. `--check` exits with code `1` when a difference exists, so it is safe to use in CI.

## Uninstall

There is no `uninstall-skill` subcommand by design. Remove the files manually:

```bash
rm .claude/skills/pyuow/SKILL.md
rm .opencode/skills/pyuow.md
```

For global installs, use the same paths under your home directory.

## See also

- [CLI reference](cli.md) — full flag list, exit codes, and paths table
