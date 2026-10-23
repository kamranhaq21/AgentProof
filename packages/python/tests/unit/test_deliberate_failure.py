"""Deliberate failure for the story 1.4 red-run proof; removed in the next commit.

Written so it passes ruff (B011 bans ``assert False``) and fails only at the pytest step.
"""


def test_deliberate_failure_for_ci_proof() -> None:
    assert 1 == 2, "story 1.4 red-run proof"
