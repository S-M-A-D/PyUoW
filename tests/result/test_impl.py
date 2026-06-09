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

    async def test_raise_for_error_should_do_nothing_if_ok(self) -> None:
        # given
        result = Result.ok(42)
        # when / then
        result.raise_for_error()
        assert result.is_ok() is True

    async def test_raise_for_error_should_raise_if_out_is_missing(
        self,
    ) -> None:
        # given
        result: Result[t.Any] = Result.empty()
        # when
        with pytest.raises(MissingOutError):
            result.raise_for_error()
        # then
        assert result.is_empty() is True

    async def test_raise_for_error_should_raise_if_out_is_error(self) -> None:
        # given
        result: Result[t.Any] = Result.error(ValueError("test"))
        # when
        with pytest.raises(ValueError, match="test"):
            result.raise_for_error()
        # then
        assert result.is_error() is True

    async def test_repr_should_wrap_ok_value(self) -> None:
        # given
        result = Result.ok(42)
        # when / then
        assert repr(result) == "Result.ok(42)"

    async def test_repr_should_wrap_error(self) -> None:
        # given
        result: Result[int] = Result.error(ValueError("boom"))
        # when / then
        assert repr(result) == "Result.error(ValueError('boom'))"

    async def test_repr_should_render_empty(self) -> None:
        # given
        result: Result[int] = Result.empty()
        # when / then
        assert repr(result) == "Result.empty()"

    async def test_map_should_transform_ok_value(self) -> None:
        # given
        result = Result.ok(2)
        # when
        mapped = result.map(lambda v: v * 3)
        # then
        assert mapped.get() == 6

    async def test_map_should_pass_through_error(self) -> None:
        # given
        error = ValueError("test")
        result: Result[int] = Result.error(error)
        fn = Mock()
        # when
        mapped = result.map(fn)
        # then
        assert mapped.is_error() is True
        fn.assert_not_called()
        with pytest.raises(ValueError, match="test"):
            mapped.get()

    async def test_map_should_pass_through_empty(self) -> None:
        # given
        result: Result[int] = Result.empty()
        fn = Mock()
        # when
        mapped = result.map(fn)
        # then
        assert mapped.is_empty() is True
        fn.assert_not_called()

    async def test_and_then_should_bind_ok_value(self) -> None:
        # given
        result = Result.ok(2)
        # when
        bound = result.and_then(lambda v: Result.ok(v * 3))
        # then
        assert bound.get() == 6

    async def test_and_then_should_propagate_returned_error(self) -> None:
        # given
        result = Result.ok(2)
        error = ValueError("inner")
        # when
        bound = result.and_then(lambda _: Result[int].error(error))
        # then
        assert bound.is_error() is True
        with pytest.raises(ValueError, match="inner"):
            bound.get()

    async def test_and_then_should_pass_through_error(self) -> None:
        # given
        result: Result[int] = Result.error(ValueError("outer"))
        fn = Mock()
        # when
        bound = result.and_then(fn)
        # then
        assert bound.is_error() is True
        fn.assert_not_called()

    async def test_and_then_should_pass_through_empty(self) -> None:
        # given
        result: Result[int] = Result.empty()
        fn = Mock()
        # when
        bound = result.and_then(fn)
        # then
        assert bound.is_empty() is True
        fn.assert_not_called()

    async def test_unwrap_or_should_return_value_for_ok(self) -> None:
        # given
        result = Result.ok(42)
        # when / then
        assert result.unwrap_or(0) == 42

    async def test_unwrap_or_should_return_default_for_error(self) -> None:
        # given
        result: Result[int] = Result.error(ValueError("test"))
        # when / then
        assert result.unwrap_or(0) == 0

    async def test_unwrap_or_should_return_default_for_empty(self) -> None:
        # given
        result: Result[int] = Result.empty()
        # when / then
        assert result.unwrap_or(0) == 0

    async def test_or_else_should_pass_through_ok(self) -> None:
        # given
        result = Result.ok(42)
        fn = Mock()
        # when
        out = result.or_else(fn)
        # then
        assert out.get() == 42
        fn.assert_not_called()

    async def test_or_else_should_call_fn_for_error(self) -> None:
        # given
        error = ValueError("test")
        result: Result[int] = Result.error(error)
        # when
        out = result.or_else(lambda _: Result.ok(0))
        # then
        assert out.get() == 0

    async def test_or_else_should_pass_through_empty(self) -> None:
        # given
        result: Result[int] = Result.empty()
        fn = Mock()
        # when
        out = result.or_else(fn)
        # then
        assert out.is_empty() is True
        fn.assert_not_called()

    async def test_unwrap_or_else_should_return_value_for_ok(self) -> None:
        # given
        result = Result.ok(42)
        # when / then
        assert result.unwrap_or_else(lambda: 0) == 42

    async def test_unwrap_or_else_should_call_fn_for_error(self) -> None:
        # given
        result: Result[int] = Result.error(ValueError("test"))
        # when / then
        assert result.unwrap_or_else(lambda: 0) == 0

    async def test_unwrap_or_else_should_call_fn_for_empty(self) -> None:
        # given
        result: Result[int] = Result.empty()
        # when / then
        assert result.unwrap_or_else(lambda: 0) == 0
