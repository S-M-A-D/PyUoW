import importlib.resources

KNOWN_TARGETS: tuple[str, ...] = ("claude", "opencode")


def load_skill_asset(target: str) -> str:
    if target not in KNOWN_TARGETS:
        raise ValueError(f"unknown target: {target!r}")
    package = "pyuow_cli.assets.skills"
    name = f"{target}.md"
    return (
        importlib.resources.files(package)
        .joinpath(name)
        .read_text(encoding="utf-8")
    )
