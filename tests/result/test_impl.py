import typing as t
from unittest.mock import Mock

import pytest

from pyuow.result import MissingOutError, Result


class TestResult:
    async def test_get_should_return_wrapped_out(self) -> None:
        # given
        mock_out = Mock()
        result = Result.ok(mock_out)
        # when
        out = result.get()
        # then
        assert out == mock_out
        assert result.is_ok() is True
        assert result.is_error() is False
        assert result.is_empty() is False

    async def test_get_should_raise_if_out_is_missing(self) -> None:
        # given
        result: Result[t.Any] = Result.empty()
        # when
        with pytest.raises(MissingOutError):
            result.get()
        # then
        assert result.is_ok() is False
        assert result.is_error() is False
        assert result.is_empty() is True

    async def test_get_should_raise_if_out_is_error(self) -> None:
        # given
        result: Result[t.Any] = Result.error(Exception("test"))
        # when
        with pytest.raises(Exception):
            result.get()
        # then
        assert result.is_ok() is False
        assert result.is_error() is True
        assert result.is_empty() is False

    async def test_or_raise_should_raise_if_out_is_error(self) -> None:
        # given
        result: Result[t.Any] = Result.error(Exception("test"))
        # when
        with pytest.raises(Exception):
            result.or_raise()
        # then
        assert result.is_ok() is False
        assert result.is_error() is True
        assert result.is_empty() is False

    async def test_repr_should_return_out_repr(self) -> None:
        # given
        mock_out = Mock()
        result: Result[Mock] = Result(mock_out)
        # when
        _repr = result.__repr__()
        # then
        assert _repr == repr(mock_out)
