from pathlib import Path
from typing import Callable, TextIO

from pyuow_cli import assets, paths, prompts


def _apply_one(
    name: str,
    target_path: Path,
    desired: str,
    *,
    check: bool,
    stdout: TextIO,
    stderr: TextIO,
) -> tuple[bool, bool]:
    if target_path.is_symlink():
        try:
            effective_path = target_path.resolve()
        except OSError:
            link_target = target_path.readlink()
            effective_path = (
                link_target
                if link_target.is_absolute()
                else target_path.parent / link_target
            )
    else:
        effective_path = target_path

    if effective_path.exists() and effective_path.is_dir():
        _ = stderr.write(f"pyuow: error: {effective_path} is a directory\n")
        return True, False

    current = ""
    if effective_path.exists():
        current = effective_path.read_text(encoding="utf-8")

    if current == desired:
        _ = stdout.write(f"{name}: up to date\n")
        return False, False

    if check:
        _ = stdout.write(f"{name}: would write\n")
        return False, True

    _ = stdout.write(f"{name}: writing\n")
    try:
        effective_path.parent.mkdir(parents=True, exist_ok=True)
        _ = effective_path.write_text(desired, encoding="utf-8", newline="\n")
    except (PermissionError, OSError) as exc:
        _ = stderr.write(f"pyuow: error: {exc}\n")
        return True, False

    return False, True


def install_skill(
    *,
    targets: tuple[str, ...] | None,
    global_: bool,
    check: bool,
    force: bool,
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
    isatty: Callable[[], bool],
    cwd: Path,
) -> int:
    if targets is None:
        if force or not isatty():
            targets = ("claude", "opencode")
        else:
            targets = prompts.select_targets(
                stdin=stdin, stdout=stdout, isatty=isatty
            )

    pairs = paths.resolve_targets(targets=targets, global_=global_, cwd=cwd)

    any_error = False
    any_diff = False

    for name, target_path in pairs:
        desired = assets.load_skill_asset(name)
        has_error, has_diff = _apply_one(
            name,
            target_path,
            desired,
            check=check,
            stdout=stdout,
            stderr=stderr,
        )
        if has_error:
            any_error = True
        if has_diff:
            any_diff = True

    if any_error:
        return 1
    if check and any_diff:
        return 1
    return 0
