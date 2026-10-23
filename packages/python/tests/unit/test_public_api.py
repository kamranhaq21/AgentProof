"""The public API is exactly ``agentproof.__all__`` (AD-15); this story adds the Suite readers."""

import agentproof
from agentproof import io, loading
from agentproof.loading.suite import parse_suite
from agentproof.runner.suite_file import load_suite


def test_public_api_names() -> None:
    assert agentproof.__all__ == ["__version__", "load_suite", "parse_suite"]


def test_the_new_names_resolve_from_the_top_level() -> None:
    assert agentproof.parse_suite is parse_suite
    assert agentproof.load_suite is load_suite


def test_read_limited_is_shell_api_not_top_level() -> None:
    assert "read_limited" not in agentproof.__all__
    assert io.__all__ == ["read_limited"]
    assert not hasattr(loading, "read_limited")
