"""The one YAML entry point (architecture AD-19; PRD FR-1, AC-1.1, AC-1.3 to AC-1.6).

``load`` turns Suite text into a plain ``dict`` with one ``yaml.SafeLoader`` subclass that
refuses, before any object is constructed, what ``yaml.safe_load`` alone would accept:

- any node whose *resolved* tag is outside the plain YAML set (``!!python/object``,
  ``!custom``, ``!!binary``, ``!!set``, the merge key ``<<``), with its line. The message
  names the tag after resolution: ``!!`` stands for the YAML namespace and any other tag is
  shown in full. When the handle the tag was written with was remapped by a ``%TAG``
  directive the message says so, because the resolved tag is then not the text the user
  wrote;
- any node whose tag does not match its shape (``!!map 5``, ``!!str [x]``), with its line;
- any anchor or alias, named, with its line, so a billion-laughs document is rejected at
  its first ``&`` and nothing is ever expanded;
- a second document, with the line of its ``---`` (or, after an explicit ``...``, the
  line where the second document's content starts);
- more than ``constants.MAX_YAML_NODES`` nodes, at the node that crosses the limit, which
  bounds the time and memory an alias-free document can cost the pure-Python loader;
- a duplicate mapping key at any depth, naming the key and the line of the second
  occurrence (PyYAML's silent last-wins merge is disabled), and a non-string key;
- a string (key or value, however it was written) holding a lone surrogate, which cannot
  be encoded as UTF-8 when a report is written, or U+FEFF anywhere but the very start of
  the document.

Mapping keys are compared as sequences of code points with no Unicode normalization, so
``é`` written as one code point and as ``e`` plus a combining accent are two keys; the
models decide what an identifier may contain.

Timestamps are kept as the text the user wrote (AD-3 stores timestamps as validated
strings), so the result holds only ``None``, ``bool``, ``int``, ``float``, ``str``,
``list`` and ``dict``. Scalar resolution is otherwise PyYAML's YAML 1.1 rule set, and the
following plain scalars resolve in ways YAML 1.2 readers do not expect (quote the value
to keep it a string):

- ``yes``, ``no``, ``true``, ``false``, ``on``, ``off`` in lower case, Capitalised, or
  UPPER case are booleans; the single letters ``y``, ``n``, ``Y`` and ``N`` stay strings;
- ``017`` is the integer 15 (a leading zero means octal); ``0o17`` stays a string;
- ``0x1A`` is the integer 26; ``1_000`` is 1000;
- ``12:30:00`` is the integer 45000 (sexagesimal);
- ``1e3`` and ``1.0e3`` stay strings (a YAML 1.1 float needs a dot and a signed
  exponent); ``1.0e+3`` is 1000.0;
- ``.inf``, ``-.inf`` and ``.nan`` are floats (the models reject non-finite numbers);
- ``2026-10-22`` and ``2026-10-22T13:05:00Z`` are kept as strings by this loader;
- a plain ``=`` is reserved by YAML 1.1 and rejected; quote it;
- a ``%YAML 1.2`` directive is accepted but the document is still read with these
  1.1 rules; ``%YAML 2.0`` is rejected.

Explicit tags are broader than plain scalars. ``!!int`` and ``!!float`` use PyYAML's
constructors without the resolver's pattern, so ``!!int`` accepts non-ASCII decimal digits
and sexagesimal text, and ``!!float 1e999`` yields infinity without ``.inf``; the models
reject non-finite numbers downstream. ``!!timestamp`` accepts any scalar text. Text that
no constructor can read (``!!int x``) is rejected.

Messages echo at most 80 characters of user text, escaped with ``repr`` so control and
bidirectional characters are never written raw. Every rejection is a ``SuiteError`` whose
``Violation.field`` is the 1-based ``line:column`` of the fault (empty when PyYAML gives
no position), and no ``yaml`` exception or other Python exception escapes. The function
receives text, never bytes or a path: the shell reads the file and enforces the size
limit with ``io.read_limited`` first (AD-1, AD-19). The module does no I/O and imports
only the standard library, PyYAML, ``agentproof.constants``, ``agentproof.errors`` and
``agentproof.models.common`` (AD-2).
"""

import re
from collections.abc import Hashable
from typing import Any, Final, NoReturn, Protocol

import yaml
from yaml.error import MarkedYAMLError
from yaml.events import AliasEvent, Event, NodeEvent, StreamEndEvent
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode
from yaml.parser import ParserError
from yaml.reader import ReaderError

from agentproof.constants import MAX_YAML_NODES
from agentproof.errors import SuiteError, Violation
from agentproof.models.common import JsonValue

__all__ = ["load"]


class Mark(Protocol):
    """The position PyYAML attaches to events, nodes and errors: 0-based line and column."""

    line: int
    column: int
    index: int


_YAML_PREFIX: Final = "tag:yaml.org,2002:"
_TIMESTAMP_TAG: Final = _YAML_PREFIX + "timestamp"
_MERGE_TAG: Final = _YAML_PREFIX + "merge"
_VALUE_TAG: Final = _YAML_PREFIX + "value"

_ALLOWED_TAGS: Final[frozenset[str]] = frozenset(
    _YAML_PREFIX + name for name in ("null", "bool", "int", "float", "str", "seq", "map")
) | {_TIMESTAMP_TAG}
"""The tags a node may resolve to or carry explicitly: the JSON-shaped scalars and
collections, plus the timestamp tag, which is constructed as text."""

_SHAPE_OF_TAG: Final[dict[str, tuple[type[Node], str]]] = {
    _YAML_PREFIX + "map": (MappingNode, "a mapping"),
    _YAML_PREFIX + "seq": (SequenceNode, "a sequence"),
}
"""The node class each collection tag requires; every other allowed tag requires a scalar."""

_SECOND_DOCUMENT: Final = "a second YAML document starts here; a Suite is a single document"
_ANCHORS_HINT: Final = "AgentProof does not expand YAML anchors and aliases, write the value out"
_MAX_ECHO: Final = 80
_NULL_SPELLINGS: Final = frozenset({"", "~", "null", "Null", "NULL"})

_TAG_START: Final = re.compile(r"!(?:(<)|((?:[0-9A-Za-z_-]*!)?))")
"""A tag as written at a node's start: ``!<verbatim>`` (group 1) or a handle (``!``,
``!!``, ``!name!``) whose characters after the first ``!`` are group 2."""

_FORBIDDEN_CHARS: Final = re.compile("[\ud800-\udfff﻿]")
"""Lone surrogates (not encodable as UTF-8) and the byte order mark inside text."""


def _clip(text: str) -> str:
    """At most ``_MAX_ECHO`` characters of ``text``, ending in ``...`` when shortened."""
    if len(text) <= _MAX_ECHO:
        return text
    return text[: _MAX_ECHO - 3] + "..."


def _quote(text: str) -> str:
    """User text for a message: clipped, then ``repr``-escaped and quoted."""
    return repr(_clip(text))


def _field(mark: Mark | None) -> str:
    """The ``Violation.field`` for a PyYAML mark: 1-based ``line:column``, or empty."""
    if mark is None:
        return ""
    return f"{mark.line + 1}:{mark.column + 1}"


def _display_tag(tag: str) -> str:
    """A resolved tag for a message: ``!!python/object`` for the YAML namespace, else full."""
    if tag == _MERGE_TAG:
        return "<<"
    if tag.startswith(_YAML_PREFIX):
        return "!!" + tag[len(_YAML_PREFIX) :]
    return tag


_SCALAR_KINDS: Final[dict[str, str]] = {
    _YAML_PREFIX + "null": "null",
    _YAML_PREFIX + "bool": "a boolean",
    _YAML_PREFIX + "int": "an integer",
    _YAML_PREFIX + "float": "a number",
    _YAML_PREFIX + "str": "a string",
    _TIMESTAMP_TAG: "a timestamp",
}


def _kind(node: Node) -> str:
    """What a composed node is, for messages: ``a mapping``, ``a sequence``, ``an integer``."""
    if isinstance(node, MappingNode):
        return "a mapping"
    if isinstance(node, SequenceNode):
        return "a sequence"
    return _SCALAR_KINDS.get(str(node.tag), "a scalar")


class _StrictLoader(yaml.SafeLoader):
    """``yaml.SafeLoader`` (the pure-Python classes) with the AD-19 rejections.

    Compose-time rules (``compose_node``, ``get_single_node``) raise at once, because an
    alias, an anchor, a foreign or mis-shaped tag, the node limit or a second document
    must stop the parse before any construction. Construction-time rules
    (``construct_mapping``, ``construct_scalar``) record every fault in ``violations`` so
    a document with several duplicate keys reports them all.
    """

    def __init__(self, text: str, source: str) -> None:
        super().__init__(text)
        self.source = source
        self.text = text
        self.node_count = 0
        self.violations: list[tuple[tuple[int, int], Violation]] = []

    def _violation(self, message: str, mark: Mark | None) -> Violation:
        return Violation(source=self.source, field=_field(mark), message=message)

    def _reject(self, message: str, mark: Mark | None) -> NoReturn:
        raise SuiteError([self._violation(message, mark)])

    def _record(self, message: str, mark: Mark | None) -> None:
        position = (mark.line, mark.column) if mark is not None else (-1, -1)
        self.violations.append((position, self._violation(message, mark)))

    def recorded_violations(self) -> list[Violation]:
        """The construction-time violations in document order."""
        return [violation for _, violation in sorted(self.violations, key=lambda item: item[0])]

    # ``peek_event`` and ``get_event`` are untyped in the PyYAML stubs; these two wrappers
    # give them the one type they return so the overrides below stay typed.

    def _peek_event(self) -> Event | None:
        event: Event | None = self.peek_event()  # type: ignore[no-untyped-call]
        return event

    def _next_event(self) -> Event | None:
        event: Event | None = self.get_event()  # type: ignore[no-untyped-call]
        return event

    # -- compose time: aliases, anchors, tags, documents, size -------------------------

    def compose_node(self, parent: Node | None, index: int) -> Node | None:
        event = self._peek_event()
        if isinstance(event, AliasEvent):
            self._reject(
                f"alias {_quote(f'*{event.anchor}')} is not allowed; {_ANCHORS_HINT} in place",
                event.start_mark,
            )
        if isinstance(event, NodeEvent) and event.anchor is not None:
            self._reject(
                f"anchor {_quote('&' + event.anchor)} is not allowed; {_ANCHORS_HINT} in place",
                event.start_mark,
            )
        self.node_count += 1
        if self.node_count > MAX_YAML_NODES:
            self._reject(
                f"the document has more than {MAX_YAML_NODES} YAML nodes; a Suite this large "
                "must be split",
                event.start_mark if event is not None else None,
            )
        node = super().compose_node(parent, index)
        if node is not None:
            self._check_tag(node)
        return node

    def _check_tag(self, node: Node) -> None:
        """Reject a resolved tag outside the plain set, or one that does not fit the node."""
        tag = str(node.tag)
        if tag not in _ALLOWED_TAGS:
            written = _TAG_START.match(self.text, node.start_mark.index)
            if tag == _VALUE_TAG and written is None:
                self._reject(
                    "a plain '=' is reserved by YAML 1.1; quote it to use it as a string",
                    node.start_mark,
                )
            what = "merge key" if tag == _MERGE_TAG else "tag"
            origin = " (resolved from a %TAG handle)" if self._handle_remapped(written) else ""
            self._reject(
                f"{what} {_quote(_display_tag(tag))}{origin} is not allowed; only plain YAML "
                "scalars, sequences and mappings are",
                node.start_mark,
            )
        node_class, expected = _SHAPE_OF_TAG.get(tag, (ScalarNode, "a scalar"))
        if not isinstance(node, node_class):
            self._reject(
                f"tag {_quote(_display_tag(tag))} expects {expected}, not {_kind(node)}",
                node.start_mark,
            )

    def _handle_remapped(self, written: re.Match[str] | None) -> bool:
        """Whether the handle a tag was written with differs from its built-in meaning."""
        if written is None or written.group(1):
            return False  # no tag written, or a verbatim ``!<...>`` tag with no handle
        handle = "!" + written.group(2)
        handles: dict[str, str] = self.tag_handles
        defaults: dict[str, str] = self.DEFAULT_TAGS
        return handles.get(handle) != defaults.get(handle)

    def get_single_node(self) -> Node | None:
        self._next_event()  # StreamStartEvent
        document: Node | None = None
        if not self.check_event(StreamEndEvent):
            document = self.compose_document()
        try:
            at_end = self.check_event(StreamEndEvent)
        except ParserError as exc:
            # After an explicit ``...`` PyYAML demands a ``---`` before more content; that
            # content is a second document.
            if exc.problem and "<document start>" in exc.problem:
                self._reject(_SECOND_DOCUMENT, exc.problem_mark)
            raise
        if not at_end:
            event = self._peek_event()
            self._reject(_SECOND_DOCUMENT, event.start_mark if event is not None else None)
        self._next_event()  # StreamEndEvent
        return document

    # -- construction time: keys, strings and timestamps --------------------------------

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Hashable, Any]:
        if not isinstance(node, MappingNode):
            self._reject(f"expected a mapping, not {_kind(node)}", node.start_mark)
        mapping: dict[Hashable, Any] = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, ScalarNode):
                self._record(
                    f"a mapping key must be a string, not {_kind(key_node)}",
                    key_node.start_mark,
                )
                continue
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                self._record(
                    f"mapping key {_quote(key_node.value)} is {_kind(key_node)}, not a string; "
                    "quote it",
                    key_node.start_mark,
                )
                continue
            if key in mapping:
                self._record(f"duplicate key {_quote(key)}", key_node.start_mark)
                continue
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping

    def construct_sequence(self, node: SequenceNode, deep: bool = False) -> list[Any]:
        if not isinstance(node, SequenceNode):
            self._reject(f"expected a sequence, not {_kind(node)}", node.start_mark)
        return super().construct_sequence(node, deep=deep)

    def construct_scalar(self, node: ScalarNode | MappingNode) -> str:
        """The scalar text, recording a fault for a lone surrogate or an inner U+FEFF.

        Escapes such as ``"\\uD800"`` produce a lone surrogate that PyYAML's reader, which
        only checks raw characters, never sees. Every string, key or value, passes here.
        """
        value = super().construct_scalar(node)
        found = _FORBIDDEN_CHARS.search(value)
        if found is not None:
            code = ord(found.group())
            what = (
                "a lone surrogate, which cannot be written as UTF-8"
                if code != 0xFEFF
                else "a byte order mark, which is only allowed at the start of the document"
            )
            self._record(f"the text contains U+{code:04X}, {what}", node.start_mark)
        return value

    def construct_timestamp_text(self, node: Node) -> str:
        """Keep a timestamp as the text written; the models validate it as a string (AD-3)."""
        if isinstance(node, ScalarNode):
            return self.construct_scalar(node)
        self._reject("a timestamp must be a scalar", node.start_mark)

    # PyYAML's scalar constructors trust the resolver's regular expressions, so an explicit
    # tag on text the regex would not have matched (``!!int x``, ``!!bool x``, ``!!int ''``),
    # or a plain value the regex accepts but ``int`` does not (``0x_``), raises
    # ``ValueError``, ``IndexError`` or ``KeyError`` out of the stock SafeLoader. These
    # wrappers turn that into a rejection.

    def construct_int_checked(self, node: Node) -> int:
        """Like ``construct_yaml_int`` but ``ValueError``/``IndexError`` become a rejection."""
        try:
            return super().construct_yaml_int(self._scalar(node, "an integer"))
        except (ValueError, IndexError):
            self._reject(f"cannot read {_quote(node.value)} as an integer", node.start_mark)

    def construct_float_checked(self, node: Node) -> float:
        """Like ``construct_yaml_float`` but ``ValueError``/``IndexError`` become a rejection."""
        try:
            return super().construct_yaml_float(self._scalar(node, "a number"))
        except (ValueError, IndexError):
            self._reject(f"cannot read {_quote(node.value)} as a number", node.start_mark)

    def construct_bool_checked(self, node: Node) -> bool:
        """``construct_yaml_bool`` with its ``KeyError`` turned into a rejection."""
        try:
            return super().construct_yaml_bool(self._scalar(node, "a boolean"))
        except KeyError:
            self._reject(f"cannot read {_quote(node.value)} as a boolean", node.start_mark)

    def construct_null_checked(self, node: Node) -> None:
        """``construct_yaml_null`` only for the spellings of null; PyYAML accepts any text."""
        scalar = self._scalar(node, "null")
        if scalar.value not in _NULL_SPELLINGS:
            self._reject(f"cannot read {_quote(node.value)} as null", node.start_mark)
        return None

    def _scalar(self, node: Node, expected: str) -> ScalarNode:
        if isinstance(node, ScalarNode):
            return node
        self._reject(f"expected {expected}, not {_kind(node)}", node.start_mark)


# ``add_constructor`` copies the constructor table onto the subclass, so ``yaml.SafeLoader``
# itself is untouched (a test asserts it).
_StrictLoader.add_constructor(_TIMESTAMP_TAG, _StrictLoader.construct_timestamp_text)
_StrictLoader.add_constructor(_YAML_PREFIX + "int", _StrictLoader.construct_int_checked)
_StrictLoader.add_constructor(_YAML_PREFIX + "float", _StrictLoader.construct_float_checked)
_StrictLoader.add_constructor(_YAML_PREFIX + "bool", _StrictLoader.construct_bool_checked)
_StrictLoader.add_constructor(_YAML_PREFIX + "null", _StrictLoader.construct_null_checked)


def _line_of_index(text: str, index: int) -> str:
    """The ``line:column`` of a character index, for errors that carry no mark."""
    index = max(0, min(index, len(text)))
    line = text.count("\n", 0, index) + 1
    column = index - text.rfind("\n", 0, index)
    return f"{line}:{column}"


def _from_yaml_error(exc: yaml.YAMLError, text: str, source: str) -> Violation:
    """One violation for a PyYAML scanner, parser, reader, composer or constructor error."""
    if isinstance(exc, MarkedYAMLError):
        problem = exc.problem or "invalid YAML"
        context = f" {exc.context}" if exc.context else ""
        mark = exc.problem_mark if exc.problem_mark is not None else exc.context_mark
        return Violation(source=source, field=_field(mark), message=_clip(f"{problem}{context}"))
    if isinstance(exc, ReaderError):
        character = exc.character
        label = f"U+{character:04X}" if isinstance(character, int) else repr(character)
        return Violation(
            source=source,
            field=_line_of_index(text, exc.position),
            message=f"{exc.reason} ({label})",
        )
    return Violation(source=source, field="", message=_clip(str(exc) or "invalid YAML"))


def _unpositioned(source: str, message: str) -> SuiteError:
    return SuiteError([Violation(source=source, field="", message=message)])


def load(text: str, *, source: str) -> dict[str, JsonValue]:
    """Parse one YAML document into a ``dict`` with string keys, or raise ``SuiteError``.

    ``source`` is the label the shell attached to the text (a path or ``<stdin>``) and is
    copied onto every ``Violation``; this function never reads a file. The caller has
    already enforced the size limit (``io.read_limited``, AD-19).

    Rejected, each as a ``SuiteError`` with the fault's 1-based ``line:column`` in
    ``Violation.field``: any anchor or alias (before expansion), any resolved tag outside
    the plain YAML set or not matching its node (before construction), a second document,
    more than ``MAX_YAML_NODES`` nodes, a duplicate or non-string mapping key and any lone
    surrogate or inner U+FEFF (every one in the document is reported), a top level that is
    not a mapping, an empty document, malformed YAML, and nesting deep enough to exhaust
    the stack. A character escape PyYAML cannot decode (``"\\U00110000"``) and any other
    exception PyYAML raises on hostile text are also ``SuiteError``, without a position.
    """
    try:
        loader = _StrictLoader(text, source)
        try:
            node = loader.get_single_node()
            if node is None:
                raise SuiteError(
                    [
                        Violation(
                            source=source,
                            field="1:1",
                            message="the document is empty; a Suite is a mapping",
                        )
                    ]
                )
            if not isinstance(node, MappingNode):
                loader._reject(
                    f"the top level is {_kind(node)}, not a mapping; a Suite is a mapping",
                    node.start_mark,
                )
            data: dict[str, JsonValue] = loader.construct_document(node)
        finally:
            loader.dispose()
    except SuiteError:
        raise
    except yaml.YAMLError as exc:
        raise SuiteError([_from_yaml_error(exc, text, source)]) from exc
    except RecursionError:
        raise _unpositioned(source, "the document nests too deeply") from None
    except (ValueError, OverflowError):
        # PyYAML's scanner calls ``chr()`` on ``\U`` escapes without a range check; above
        # U+10FFFF that is a ``ValueError``, and on CPython 3.12 a value that does not fit
        # a C int (``\UFFFFFFFF``) is an ``OverflowError``.
        raise _unpositioned(
            source, "the document has a character escape that is not a valid Unicode character"
        ) from None
    except Exception as exc:
        # Defense in depth for an input that trips a PyYAML bug: still an input fault.
        # Only the exception type is named, never its text, which may echo the input.
        raise _unpositioned(
            source, f"the document could not be parsed ({type(exc).__name__})"
        ) from None
    violations = loader.recorded_violations()
    if violations:
        raise SuiteError(violations)
    return data
