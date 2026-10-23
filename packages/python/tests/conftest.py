"""Test-session configuration shared by every test under ``tests/``.

Hypothesis (story 2.6): one profile, loaded here so it applies before any test module
is imported. ``derandomize=True`` derives the example sequence from the test itself, so
a run on CI or locally replays the same examples and a failure reproduces on the next
run without a saved database; ``database=None`` keeps Hypothesis from writing a
``.hypothesis/`` directory into the tree; ``deadline=None`` because CI runners' timing
varies and the properties measure correctness, not speed. ``max_examples`` is set
explicitly on every property, not here.
"""

from hypothesis import HealthCheck, settings

settings.register_profile(
    "agentproof",
    derandomize=True,
    database=None,
    deadline=None,
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("agentproof")
