"""CLI entrypoint for pyuow."""

import argparse
import importlib.metadata
import sys
from collections.abc import Sequence
from pathlib import Path

from pyuow_cli.install_skill import install_skill


class _VersionAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[str] | None,
        option_string: str | None = None,
    ) -> None:
        try:
            version = importlib.metadata.version("pyuow")
        except importlib.metadata.PackageNotFoundError:
            print("pyuow (unknown version)")
        else:
            print(f"pyuow {version}")
        parser.exit(0)


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="pyuow")
    _ = parser.add_argument("--version", action=_VersionAction, nargs=0)

    subparsers = parser.add_subparsers(required=True, dest="command")
    install_parser = subparsers.add_parser("install-skill")
    _ = install_parser.add_argument(
        "--target", choices=["claude", "opencode", "both"]
    )
    _ = install_parser.add_argument(
        "--global", action="store_true", dest="global_"
    )
    _ = install_parser.add_argument("--check", action="store_true")
    _ = install_parser.add_argument("--force", action="store_true")

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    if args.command == "install-skill":
        targets: tuple[str, ...] | None
        if args.target == "both":
            targets = ("claude", "opencode")
        elif args.target is None:
            targets = None
        else:
            targets = (args.target,)

        try:
            return install_skill(
                targets=targets,
                global_=args.global_,
                check=args.check,
                force=args.force,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
                isatty=sys.stdin.isatty,
                cwd=Path.cwd(),
            )
        except KeyboardInterrupt:
            return 130

    return 2  # pragma: no cover
