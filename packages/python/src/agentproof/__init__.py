"""AgentProof: local-first testing and regression framework for tool-using AI agents.

The public API is exactly ``__all__`` (architecture AD-15). ``pyproject.toml`` is the
single source of the version; it is read once here from the installed package
metadata. The lookup key is the distribution name, so it must change together with
the ``name`` field in ``pyproject.toml`` when OQ-1 is decided.
"""

from importlib.metadata import version as _distribution_version

from agentproof.loading.suite import parse_suite
from agentproof.runner.suite_file import load_suite

__version__: str = _distribution_version("agentproof")

__all__ = ["__version__", "load_suite", "parse_suite"]
