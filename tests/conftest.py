import os
import sys

import pytest
from _pytest.nodes import Item


def pytest_runtest_setup(item: Item) -> None:
    is_ci = os.getenv("GITHUB_ACTIONS") == "true"
    is_unsupported_platform = sys.platform in ["win32", "darwin"]

    for _ in item.iter_markers(name="skip_on_ci"):
        if is_ci and is_unsupported_platform:
            pytest.skip(f"Does not run on {sys.platform} inside GitHub Action")
