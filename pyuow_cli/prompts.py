from typing import Callable, TextIO

__all__ = ("select_targets",)

_DEFAULT_TARGETS: tuple[str, ...] = ("claude", "opencode")

_MENU = (
    "Select targets:\n"
    "  1) Claude\n"
    "  2) OpenCode\n"
    "  3) Both\n"
    "Press Enter for both: "
)
_INVALID = "Invalid choice. Please select 1, 2, or 3.\n"


def select_targets(
    *,
    stdin: TextIO,
    stdout: TextIO,
    isatty: Callable[[], bool],
) -> tuple[str, ...]:
    if not isatty():
        return _DEFAULT_TARGETS

    while True:
        _ = stdout.write(_MENU)
        try:
            raw = stdin.readline()
        except EOFError:
            return _DEFAULT_TARGETS

        if raw == "":
            return _DEFAULT_TARGETS

        choice = raw.strip()
        if choice == "" or choice == "3":
            return _DEFAULT_TARGETS
        if choice == "1":
            return ("claude",)
        if choice == "2":
            return ("opencode",)

        _ = stdout.write(_INVALID)
