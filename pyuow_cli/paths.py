from pathlib import Path

TARGET_NAMES: tuple[str, ...] = ("claude", "opencode")


def claude_target(*, global_: bool, cwd: Path) -> Path:
    base = Path.home() if global_ else cwd
    return base / ".claude" / "skills" / "pyuow" / "SKILL.md"


def opencode_target(*, global_: bool, cwd: Path) -> Path:
    base = Path.home() if global_ else cwd
    if global_:
        return base / ".config" / "opencode" / "skills" / "pyuow.md"
    return base / ".opencode" / "skills" / "pyuow.md"


def resolve_targets(
    *,
    targets: tuple[str, ...],
    global_: bool,
    cwd: Path,
) -> list[tuple[str, Path]]:
    resolved: list[tuple[str, Path]] = []
    for target in targets:
        if target == "claude":
            resolved.append((target, claude_target(global_=global_, cwd=cwd)))
        elif target == "opencode":
            resolved.append(
                (target, opencode_target(global_=global_, cwd=cwd))
            )
        else:
            raise ValueError(f"unknown target: {target!r}")
    return resolved
