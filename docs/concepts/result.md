# Result

`Result` is the return envelope for every flow. It's a frozen dataclass with three states:

- **Ok** — wraps a success value.
- **Error** — wraps an exception.
- **Empty** — represents "no value".

```python
from pyuow import Result


ok    = Result.ok(42)
err   = Result.error(ValueError("nope"))
empty = Result.empty()
```

## State predicates

```python
ok.is_ok()       # True
err.is_error()   # True
empty.is_empty() # True
```

## Unwrapping

`.get()` returns the value for `ok` results, raises the wrapped exception for `error` results, and raises `MissingOutError` for `empty` results.

```python
ok.get()         # 42
err.get()        # raises ValueError("nope")
empty.get()      # raises MissingOutError
```

`.raise_for_error()` validates without returning. Use it in side-effect flows where the success value is irrelevant but you still want failures to surface.

```python
ok.raise_for_error()     # no-op
err.raise_for_error()    # raises ValueError("nope")
empty.raise_for_error()  # raises MissingOutError
```

`.unwrap_or(default)` returns the value for `ok`, otherwise returns the supplied default. It never raises.

```python
ok.unwrap_or(0)     # 42
err.unwrap_or(0)    # 0
empty.unwrap_or(0)  # 0
```

`.unwrap_or_else(fn)` returns the value for `ok`. For `error` or `empty`, it calls `fn()` and returns that result instead.

```python
ok.unwrap_or_else(lambda: 0)     # 42
err.unwrap_or_else(lambda: 0)    # 0
empty.unwrap_or_else(lambda: 0)  # 0
```

## Transforming

### `.map(fn)`

Apply a function to the ok value. Error and empty pass through unchanged.

```python
Result.ok(2).map(lambda x: x * 3)        # Result.ok(6)
Result.error(ValueError()).map(str)      # Result.error(ValueError())
Result.empty().map(lambda x: x * 3)      # Result.empty()
```

The transformer is not called for non-ok results.

### `.and_then(fn)`

Bind another `Result`-returning operation onto an ok value. Error and empty short-circuit.

```python
def parse(s: str) -> Result[int]:
    try:
        return Result.ok(int(s))
    except ValueError as e:
        return Result.error(e)


Result.ok("42").and_then(parse)    # Result.ok(42)
Result.ok("nope").and_then(parse)  # Result.error(ValueError(...))
Result.empty().and_then(parse)     # Result.empty()
```

`.and_then` is the classic monadic bind — it lets you chain operations that themselves can fail without un-nesting Results.

### `.or_else(fn)`

Recover from an error by calling `fn(exc)` and returning its `Result`. `ok` and `empty` pass through unchanged.

```python
Result.ok(42).or_else(lambda _: Result.ok(0))              # Result.ok(42)
Result.error(ValueError()).or_else(lambda _: Result.ok(0)) # Result.ok(0)
Result.empty().or_else(lambda _: Result.ok(0))             # Result.empty()
```

## Repr

`repr()` wraps the value in its constructor form so logs are unambiguous:

```python
repr(Result.ok(42))                       # 'Result.ok(42)'
repr(Result.error(ValueError("boom")))    # "Result.error(ValueError('boom'))"
repr(Result.empty())                      # 'Result.empty()'
```

## When to use which

| You want                              | Use                          |
| ------------------------------------- | ---------------------------- |
| Raise on failure, return on success   | `.get()`                     |
| Raise on failure, ignore the value    | `.raise_for_error()`         |
| Fall back to a default                | `.unwrap_or(default)`        |
| Fall back to a computed value         | `.unwrap_or_else(fn)`        |
| Transform success only                | `.map(fn)`                   |
| Chain a fallible operation            | `.and_then(fn)`              |
| Recover from an error                 | `.or_else(fn)`               |
| Inspect without unwrapping            | `.is_ok()` / `.is_error()` / `.is_empty()` |

## Reference

- [`pyuow.result`](../api/result.md) — `Result`, `MissingOutError`
