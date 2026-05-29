"""PyUoW command-line interface.

Currently provides a single subcommand: `install-skill`, which makes the
bundled AI agent skill files (in `pyuow/_skill/`) available to Claude Code,
opencode, or Codex.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from importlib.resources import files as _resource_files
from pathlib import Path
from typing import Optional

SKILL_DIR_NAME = "pyuow"


def _skill_source_dir() -> Path:
    """Return the absolute path to the bundled `_skill/` directory."""
    resource = _resource_files("pyuow._skill")
    # importlib.resources returns a Traversable; for installed packages it's
    # backed by a real path. Coerce to Path; if the package is zipped (rare),
    # str(resource) still gives a usable representation but symlinks won't
    # work — copy fallback engages.
    return Path(str(resource))


def _resolve_target(args: argparse.Namespace) -> Path:
    if args.path:
        return Path(args.path).expanduser().resolve() / SKILL_DIR_NAME
    if args.global_:
        return Path.home() / ".claude" / "skills" / SKILL_DIR_NAME
    if args.codex:
        return Path.home() / ".agents" / "skills" / SKILL_DIR_NAME
    # default: project-local
    return Path.cwd() / ".claude" / "skills" / SKILL_DIR_NAME


def _install_skill(args: argparse.Namespace) -> int:
    source = _skill_source_dir()
    target = _resolve_target(args)

    if not source.is_dir():
        print(
            f"error: bundled skill directory not found at {source}",
            file=sys.stderr,
        )
        return 2

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() or target.is_symlink():
        if not args.force:
            print(
                f"error: {target} already exists. Use --force to overwrite.",
                file=sys.stderr,
            )
            return 1
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)

    mode = "copy"
    if not args.copy:
        try:
            os.symlink(source, target, target_is_directory=True)
            mode = "symlink"
        except (OSError, NotImplementedError):
            mode = "copy"

    if mode == "copy":
        shutil.copytree(source, target)

    print(f"Installed pyuow skill -> {target} ({mode})")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyuow",
        description="pyuow command-line utilities.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser(
        "install-skill",
        help=(
            "Install the bundled AI agent skill into ~/.claude/skills, a "
            "project-local .claude/skills, or ~/.agents/skills (Codex)."
        ),
    )
    scope = install.add_mutually_exclusive_group()
    scope.add_argument(
        "--project",
        action="store_true",
        help="Install to <cwd>/.claude/skills/pyuow (default).",
    )
    scope.add_argument(
        "--global",
        dest="global_",
        action="store_true",
        help="Install to ~/.claude/skills/pyuow.",
    )
    scope.add_argument(
        "--codex",
        action="store_true",
        help="Install to ~/.agents/skills/pyuow.",
    )
    scope.add_argument(
        "--path",
        metavar="DIR",
        help="Install to a custom skills directory (DIR/pyuow).",
    )
    install.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of creating a symlink.",
    )
    install.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing target directory.",
    )
    install.set_defaults(func=_install_skill)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
