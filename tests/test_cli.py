from __future__ import annotations

import importlib.metadata
import io
import re
import runpy
import sys
from pathlib import Path
from typing import Callable, TextIO
from unittest.mock import Mock

import pytest

from pyuow_cli import assets, prompts
from pyuow_cli.assets import KNOWN_TARGETS, load_skill_asset
from pyuow_cli.install_skill import install_skill
from pyuow_cli.main import main
from pyuow_cli.paths import resolve_targets
from pyuow_cli.prompts import select_targets


def _noop_isatty() -> bool:
    return False


def _yes_isatty() -> bool:
    return True


def _canonical_python_blocks(target: str) -> list[str]:
    body = load_skill_asset(target).split("---", 2)[2]
    blocks: list[str] = re.findall(r"```python\n(.*?)\n```", body, re.S)
    assert blocks, f"missing python block for {target}"
    return blocks


class TestAssetLoader:
    def test_load_skill_asset_should_return_claude_content(self) -> None:
        # when / then
        assert load_skill_asset("claude").startswith("---\nname: pyuow\n")

    def test_load_skill_asset_should_return_opencode_content(self) -> None:
        # when / then
        assert load_skill_asset("opencode").startswith("---\nname: pyuow\n")

    @pytest.mark.parametrize(
        "target", ["unknown", "../claude", "claude/../opencode"]
    )
    def test_load_skill_asset_should_raise_on_unknown_target(
        self, target: str
    ) -> None:
        # when / then
        with pytest.raises(ValueError, match=r"^unknown target: "):
            _ = load_skill_asset(target)

    def test_known_targets_should_be_claude_and_opencode(self) -> None:
        # when / then
        assert KNOWN_TARGETS == ("claude", "opencode")


class TestSkillCanonicalExample:
    def test_canonical_example_should_execute_and_match(self) -> None:
        # given
        claude_code_blocks = _canonical_python_blocks("claude")
        opencode_code_blocks = _canonical_python_blocks("opencode")
        # when / then
        assert opencode_code_blocks == claude_code_blocks


class TestPaths:
    def test_resolve_targets_should_raise_on_unknown_target(
        self, tmp_path: Path
    ) -> None:
        # when / then
        with pytest.raises(ValueError, match=r"^unknown target: 'bogus'$"):
            _ = resolve_targets(
                targets=("bogus",), global_=False, cwd=tmp_path
            )

    def test_resolve_targets_should_return_both_targets(
        self, tmp_path: Path
    ) -> None:
        # when
        result = resolve_targets(
            targets=("claude", "opencode"), global_=False, cwd=tmp_path
        )
        # then
        assert len(result) == 2
        assert result[0][0] == "claude"
        assert (
            result[0][1]
            == tmp_path / ".claude" / "skills" / "pyuow" / "SKILL.md"
        )
        assert result[1][0] == "opencode"
        assert result[1][1] == tmp_path / ".opencode" / "skills" / "pyuow.md"


class TestPrompts:
    def test_select_targets_should_return_defaults_off_tty(self) -> None:
        # given
        stdin = io.StringIO()
        stdout = io.StringIO()
        # when
        result = select_targets(
            stdin=stdin, stdout=stdout, isatty=_noop_isatty
        )
        # then
        assert result == ("claude", "opencode")
        assert stdout.getvalue() == ""

    def test_select_targets_should_return_claude_on_choice_one(
        self,
    ) -> None:
        # given
        stdin = io.StringIO("1\n")
        stdout = io.StringIO()
        # when
        result = select_targets(stdin=stdin, stdout=stdout, isatty=_yes_isatty)
        # then
        assert result == ("claude",)
        assert "Select targets:" in stdout.getvalue()

    def test_select_targets_should_return_opencode_on_choice_two(
        self,
    ) -> None:
        # given
        stdin = io.StringIO("2\n")
        stdout = io.StringIO()
        # when
        result = select_targets(stdin=stdin, stdout=stdout, isatty=_yes_isatty)
        # then
        assert result == ("opencode",)

    def test_select_targets_should_return_defaults_on_choice_three(
        self,
    ) -> None:
        # given
        stdin = io.StringIO("3\n")
        stdout = io.StringIO()
        # when
        result = select_targets(stdin=stdin, stdout=stdout, isatty=_yes_isatty)
        # then
        assert result == ("claude", "opencode")

    def test_select_targets_should_return_defaults_on_empty_choice(
        self,
    ) -> None:
        # given
        stdin = io.StringIO("\n")
        stdout = io.StringIO()
        # when
        result = select_targets(stdin=stdin, stdout=stdout, isatty=_yes_isatty)
        # then
        assert result == ("claude", "opencode")

    def test_select_targets_should_return_defaults_on_empty_readline(
        self,
    ) -> None:
        # given
        stdin = io.StringIO("")
        stdout = io.StringIO()
        # when
        result = select_targets(stdin=stdin, stdout=stdout, isatty=_yes_isatty)
        # then
        assert result == ("claude", "opencode")

    def test_select_targets_should_retry_on_invalid_choice(self) -> None:
        # given
        stdin = io.StringIO("99\n1\n")
        stdout = io.StringIO()
        # when
        result = select_targets(stdin=stdin, stdout=stdout, isatty=_yes_isatty)
        # then
        assert result == ("claude",)
        assert "Invalid choice" in stdout.getvalue()

    def test_select_targets_should_return_defaults_on_eof_error(self) -> None:
        # given
        stdin = Mock(spec=io.StringIO)
        stdin.readline = Mock(side_effect=EOFError())
        stdout = io.StringIO()
        # when
        result = select_targets(stdin=stdin, stdout=stdout, isatty=_yes_isatty)
        # then
        assert result == ("claude", "opencode")


class TestInstallSkill:
    def test_install_skill_should_install_both_targets(
        self, tmp_path: Path
    ) -> None:
        # given
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude", "opencode"),
            global_=False,
            check=False,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 0
        claude_path = tmp_path / ".claude" / "skills" / "pyuow" / "SKILL.md"
        opencode_path = tmp_path / ".opencode" / "skills" / "pyuow.md"
        assert claude_path.exists()
        assert opencode_path.exists()
        assert "claude: writing" in stdout.getvalue()
        assert "opencode: writing" in stdout.getvalue()

    def test_install_skill_check_should_return_one_when_absent(
        self, tmp_path: Path
    ) -> None:
        # given
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude", "opencode"),
            global_=False,
            check=True,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 1
        assert "claude: would write" in stdout.getvalue()
        assert "opencode: would write" in stdout.getvalue()
        assert not (
            tmp_path / ".claude" / "skills" / "pyuow" / "SKILL.md"
        ).exists()
        assert not (tmp_path / ".opencode" / "skills" / "pyuow.md").exists()

    def test_install_skill_check_should_return_zero_when_identical(
        self, tmp_path: Path
    ) -> None:
        # given
        claude_path = tmp_path / ".claude" / "skills" / "pyuow" / "SKILL.md"
        opencode_path = tmp_path / ".opencode" / "skills" / "pyuow.md"
        claude_path.parent.mkdir(parents=True)
        opencode_path.parent.mkdir(parents=True)
        desired = assets.load_skill_asset("claude")
        _ = claude_path.write_text(desired, encoding="utf-8", newline="\n")
        desired_o = assets.load_skill_asset("opencode")
        _ = opencode_path.write_text(desired_o, encoding="utf-8", newline="\n")
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude", "opencode"),
            global_=False,
            check=True,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 0
        assert "claude: up to date" in stdout.getvalue()
        assert "opencode: up to date" in stdout.getvalue()

    def test_install_skill_check_should_return_one_when_different(
        self, tmp_path: Path
    ) -> None:
        # given
        claude_path = tmp_path / ".claude" / "skills" / "pyuow" / "SKILL.md"
        opencode_path = tmp_path / ".opencode" / "skills" / "pyuow.md"
        claude_path.parent.mkdir(parents=True)
        opencode_path.parent.mkdir(parents=True)
        _ = claude_path.write_text("wrong", encoding="utf-8", newline="\n")
        _ = opencode_path.write_text("wrong", encoding="utf-8", newline="\n")
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude", "opencode"),
            global_=False,
            check=True,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 1
        assert "claude: would write" in stdout.getvalue()
        assert "opencode: would write" in stdout.getvalue()

    def test_install_skill_should_install_claude_only(
        self, tmp_path: Path
    ) -> None:
        # given
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude",),
            global_=False,
            check=False,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 0
        assert (
            tmp_path / ".claude" / "skills" / "pyuow" / "SKILL.md"
        ).exists()
        assert not (tmp_path / ".opencode" / "skills" / "pyuow.md").exists()

    def test_install_skill_should_install_to_global_paths(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # given
        fake_home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude", "opencode"),
            global_=True,
            check=False,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path / "proj",
        )
        # then
        assert result == 0
        assert (
            fake_home / ".claude" / "skills" / "pyuow" / "SKILL.md"
        ).exists()
        assert (
            fake_home / ".config" / "opencode" / "skills" / "pyuow.md"
        ).exists()

    def test_install_skill_should_preserve_symlink(
        self, tmp_path: Path
    ) -> None:
        # given
        link_dir = tmp_path / ".claude" / "skills" / "pyuow"
        link_dir.mkdir(parents=True)
        real_file = tmp_path / "real_skill.md"
        link_path = link_dir / "SKILL.md"
        link_path.symlink_to(real_file)
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude",),
            global_=False,
            check=False,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 0
        assert real_file.exists()
        assert link_path.is_symlink()
        assert "claude: writing" in stdout.getvalue()

    def test_install_skill_should_return_one_on_permission_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # given
        def _raise(*args: object, **kwargs: object) -> None:
            _ = (args, kwargs)
            raise PermissionError("denied")

        monkeypatch.setattr(Path, "mkdir", _raise)
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude",),
            global_=False,
            check=False,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 1
        assert "pyuow: error: denied" in stderr.getvalue()

    def test_install_skill_should_default_to_both_off_tty(
        self, tmp_path: Path
    ) -> None:
        # given
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=None,
            global_=False,
            check=False,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 0
        assert (
            tmp_path / ".claude" / "skills" / "pyuow" / "SKILL.md"
        ).exists()
        assert (tmp_path / ".opencode" / "skills" / "pyuow.md").exists()

    def test_install_skill_should_prompt_when_no_target_on_tty(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # given
        def _select(
            *, stdin: TextIO, stdout: TextIO, isatty: Callable[[], bool]
        ) -> tuple[str, ...]:
            _ = (stdin, stdout, isatty)
            return ("claude",)

        monkeypatch.setattr(prompts, "select_targets", _select)
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=None,
            global_=False,
            check=False,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_yes_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 0
        assert (
            tmp_path / ".claude" / "skills" / "pyuow" / "SKILL.md"
        ).exists()
        assert not (tmp_path / ".opencode" / "skills" / "pyuow.md").exists()

    def test_install_skill_should_return_one_when_target_is_directory(
        self, tmp_path: Path
    ) -> None:
        # given
        guard = tmp_path / ".claude" / "skills" / "pyuow" / "SKILL.md"
        guard.parent.mkdir(parents=True)
        guard.mkdir()
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude",),
            global_=False,
            check=False,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 1
        assert "pyuow: error: " in stderr.getvalue()
        assert "is a directory" in stderr.getvalue()

    def test_install_skill_should_handle_broken_symlink(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # given
        link_dir = tmp_path / ".claude" / "skills" / "pyuow"
        link_dir.mkdir(parents=True)
        link_path = link_dir / "SKILL.md"
        link_path.symlink_to(tmp_path / "nonexistent")

        def _bad_resolve(self: Path, strict: bool = False) -> Path:
            _ = (self, strict)
            raise OSError("broken link")

        monkeypatch.setattr(Path, "resolve", _bad_resolve)
        stdin = io.StringIO()
        stdout = io.StringIO()
        stderr = io.StringIO()
        # when
        result = install_skill(
            targets=("claude",),
            global_=False,
            check=False,
            force=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            isatty=_noop_isatty,
            cwd=tmp_path,
        )
        # then
        assert result == 0
        assert link_path.is_symlink()


class TestMain:
    def test_main_should_print_version(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # when
        assert main(["--version"]) == 0
        captured = capsys.readouterr()
        # then
        version = importlib.metadata.version("pyuow")
        assert captured.out == f"pyuow {version}\n"
        assert captured.err == ""

    # given
    def test_main_should_print_help(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # when
        assert main(["--help"]) == 0
        captured = capsys.readouterr()
        # then
        assert "usage: pyuow" in captured.out
        assert captured.err == ""

    def test_main_install_skill_should_print_help(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # when
        assert main(["install-skill", "--help"]) == 0
        captured = capsys.readouterr()
        # then
        assert "usage: pyuow install-skill" in captured.out
        assert captured.err == ""

    def test_main_install_skill_should_pass_claude_and_check(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # given
        calls: list[dict[str, object]] = []

        def _fake(**kwargs: object) -> int:
            calls.append(kwargs)
            return 0

        monkeypatch.setattr("pyuow_cli.main.install_skill", _fake)
        # when
        assert main(["install-skill", "--target", "claude", "--check"]) == 0
        # then
        assert len(calls) == 1
        assert calls[0]["targets"] == ("claude",)
        assert calls[0]["check"] is True
        assert calls[0]["force"] is False
        assert calls[0]["global_"] is False

    def test_main_install_skill_should_pass_both_and_global(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # given
        calls: list[dict[str, object]] = []

        def _fake(**kwargs: object) -> int:
            calls.append(kwargs)
            return 0

        # given
        monkeypatch.setattr("pyuow_cli.main.install_skill", _fake)
        # when
        assert main(["install-skill", "--target", "both", "--global"]) == 0
        # then
        assert len(calls) == 1
        assert calls[0]["targets"] == ("claude", "opencode")
        assert calls[0]["global_"] is True

    def test_main_should_return_nonzero_for_bad_target(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # when
        assert main(["install-skill", "--target", "bogus"]) != 0
        captured = capsys.readouterr()
        # then
        assert (
            "error" in captured.err.lower()
            or "invalid choice" in captured.err.lower()
        )

    def test_main_should_return_nonzero_for_bogus_subcommand(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # when
        assert main(["bogus-subcommand"]) != 0
        captured = capsys.readouterr()
        # then
        assert (
            "error" in captured.err.lower()
            or "invalid choice" in captured.err.lower()
        )

    def test_main_should_return_130_on_keyboard_interrupt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # given
        def _fake(**_kwargs: object) -> int:
            raise KeyboardInterrupt()

        monkeypatch.setattr("pyuow_cli.main.install_skill", _fake)
        # when / then
        assert main(["install-skill"]) == 130

    def test_main_should_print_unknown_version_when_package_not_found(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # given
        def _fake(_name: str) -> str:
            raise importlib.metadata.PackageNotFoundError("pyuow")

        monkeypatch.setattr("importlib.metadata.version", _fake)
        # when
        assert main(["--version"]) == 0
        captured = capsys.readouterr()
        # then
        assert captured.out == "pyuow (unknown version)\n"
        assert captured.err == ""

    def test_main_should_use_sys_argv_when_no_args_passed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # given
        monkeypatch.setattr("sys.argv", ["pyuow", "--version"])
        # when / then
        assert main() == 0

    def test_main_module_should_run_via_runpy(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # given
        monkeypatch.setattr("sys.argv", ["pyuow", "--version"])
        sys.modules.pop("pyuow_cli.__main__", None)
        # when / then
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("pyuow_cli", run_name="__main__")
        assert exc_info.value.code == 0
