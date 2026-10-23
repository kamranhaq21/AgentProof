"""The one text scrubber (architecture AD-10; PRD AC-28.2).

``scrub_text`` is shared by the console filter (``io.console``, story 3.5) and the Trace
``redact`` function (epic 5), so the marker and the span rule exist once. Pure: no I/O,
no state.
"""

from collections.abc import Iterable, Iterator

from agentproof.constants import REDACTED

__all__ = ["scrub_text"]


def _occurrences(text: str, value: str) -> Iterator[tuple[int, int]]:
    """Every ``(start, end)`` of ``value`` in ``text``, overlapping occurrences included."""
    start = text.find(value)
    while start != -1:
        yield start, start + len(value)
        start = text.find(value, start + 1)


def scrub_text(text: str, secret_values: Iterable[str]) -> str:
    """Replace every character covered by any occurrence of any secret value with the marker.

    All occurrences of all values are located in the original text first (overlapping ones
    included), overlapping or touching spans are merged, and each merged span becomes one
    marker. So two values that overlap without either containing the other (``abcXY`` and
    ``XYdef`` in ``abcXYdef``) leave no fragment of either, and the result does not depend
    on the order of ``secret_values``. Empty values contribute nothing (an empty string
    would match between every character); ARCH-6 sets no length floor for the rest.
    """
    spans: list[tuple[int, int]] = []
    for value in {value for value in secret_values if value}:
        spans.extend(_occurrences(text, value))
    if not spans:
        return text
    spans.sort()
    merged: list[list[int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    pieces: list[str] = []
    cursor = 0
    for start, end in merged:
        pieces.append(text[cursor:start])
        pieces.append(REDACTED)
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)
