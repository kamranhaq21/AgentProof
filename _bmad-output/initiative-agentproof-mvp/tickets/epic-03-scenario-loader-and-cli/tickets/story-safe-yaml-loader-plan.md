---
title: 'Safe YAML loader'
type: 'feature'
ticket: '2'
created: '2026-10-23'
status: done
baseline_revision: 'fca6286427e55f823cb7560090bf0c6a491eecc5'
route: 'full'
route_source: 'pinned'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing in the package can turn Suite text into data yet, and `yaml.safe_load` alone would accept four things a Suite must never carry: a custom tag (`!!python/object` constructs an object before any model sees it), a duplicate mapping key (PyYAML's silent last-wins merge), an anchor or alias (the billion-laughs expansion), and a second `---` document. Every later story in epic 3 (`parse_suite`, `validate`, `init`) and every Trace or Report reader that reads YAML rests on this one entry point (story 3.2; epic 3 R1; PRD FR-1, AC-1.1, AC-1.3 to AC-1.6; spine AD-19).

**Approach:** Add `agentproof.loading.yaml_safe` with one function, `load(text: str, *, source: str) -> dict[str, JsonValue]`, built on one `yaml.SafeLoader` subclass (the pure-Python loader classes, never `CSafeLoader`). The subclass rejects at **compose time**, before any object is constructed: every alias and every anchor (named, with the line of the `*` or `&`), every resolved tag outside the plain YAML set (null, bool, int, float, str, seq, map, timestamp; named as resolved, so `!!python/object/apply:os.system` and `!shout` both appear in the message), a tag that does not fit its node (`!!map 5`), a second document (the line of its `---`, or of the content after an explicit `...`), and a document of more than `constants.MAX_YAML_NODES` nodes. At **construction time** it rejects duplicate keys (naming the key and the line of the second occurrence), non-string keys, and strings holding a lone surrogate or an inner U+FEFF, collecting every such fault in the document before raising. A non-mapping or empty top level is rejected because a Suite is a mapping. Timestamps are constructed as the text the user wrote (AD-3 stores timestamps as validated strings; PyYAML would otherwise return `datetime` objects). Every rejection, including PyYAML's own scanner, parser, reader, and composer errors, a `RecursionError` from pathological nesting, an undecodable `\U` escape, and any other exception an input provokes inside PyYAML, is raised as `SuiteError` carrying `Violation(source, "<line>:<column>", message)`; no `yaml` exception type and no other Python exception escapes. Per AD-19 the size limit is enforced by `io.read_limited` (epic 5 / story 3.3) *before* this function, so `load` takes text, never bytes or a path, and never does I/O (AD-1).

**Also routed here (epic-1 retrospective finding 4):** AD-19 says `pickle`, `marshal`, `eval`, `exec`, and `yaml.load` are banned by the ruff list; they were not, and the `TID251` per-file-ignores exempt the shell packages. `pyproject.toml` gains ruff flake8-bandit rules `S102` (exec), `S307` (eval), `S301` (pickle.loads), `S302` (marshal), `S506` (yaml.load) in `select` for every file including shell packages, devtools, and tests, plus `TID251` bans for the `pickle`, `marshal`, and `shelve` modules; the only new per-file-ignore is `S301` on `tests/unit/test_errors_taxonomy.py`, which deliberately round-trips an exception through `pickle.loads`.

## Boundaries & Constraints

**Always:** `loading/yaml_safe.py` imports only the standard library, PyYAML, `agentproof.constants`, `agentproof.errors`, and `agentproof.models.common` (AD-2: `loading` sits above `models`, `constants`, `errors`); it uses none of the names AD-1 bans (purity checker and TID251 apply) and performs no I/O; the loader class subclasses `yaml.SafeLoader` (pure Python) and `load` instantiates it directly rather than calling `yaml.load`, so rule S506 cannot be tripped and the module contains no `yaml.load` or `safe_load` call; every rejection is a `SuiteError` built from `errors.Violation` (no new exception class; `errors.py` untouched); the result is a plain `dict` with `str` keys and PyYAML's native scalars (`int`, `float`, `bool`, `None`, `str`, `list`, `dict`); `${VAR}` passes through unchanged (AC-1.3); message text echoes at most 80 characters of user input, escaped with `repr`; the fixture files are LF; `mypy --strict` passes on `src`; no `from __future__ import annotations`.

**Never:** no model validation (the result is a dict; `parse_suite` is story 3.3); no file reading or size check (story 3.3's `io.read_limited`); no changes to `errors.py`, `models/*`, `.importlinter`, or the check entry point; no network; no new runtime dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Custom tag (criterion 1, AC-1.1) | `description: !shout "hello"` on line 3 | rejected at compose time, nothing constructed | `SuiteError`, one `Violation(source, "3:14", ...)` naming `!shout` |
| Python object tag (criterion 1, AC-1.1) | `suite: !!python/object/apply:os.system ["echo pwned"]` on line 2 | rejected at compose time; `construct_document` never runs | `SuiteError` at `2:8` naming `!!python/object/apply:os.system` |
| Other tags | `!!python/name:os.system`, `!!python/module:os`, verbatim `!<tag:example.com,2026:x>`, `!!binary`, `!!set`, `!!omap`, `!!pairs`, merge key `<<` | rejected | `SuiteError` naming the tag (`<<` named as the merge key) |
| `%TAG` rewriting | `%TAG !e! tag:example.com,2026:` then `!e!x` | rejected naming the resolved tag and `(resolved from a %TAG handle)`; a directive for a handle the tag did not use adds no note | `SuiteError` |
| Tag does not fit node | `!!map 5`, `!!map [x, y]`, `!!seq {x: 1}`, `!!str [x]`, `!!int [1]` | rejected at compose time | `SuiteError` at the node, `tag '!!map' expects a mapping, not a scalar` |
| Typed scalar unreadable | `!!int x`, `!!int ''`, `!!float x`, `!!bool x`, `!!null x`, `0x_`, `0b_`, a 5000-digit integer | rejected | `SuiteError`, `cannot read '...' as an integer` (echo clipped to 80 characters) |
| Plain standard tags | `!!str 123`, `!!int "7"`, unquoted `2026-10-22T13:05:00Z` | accepted; the timestamp is the text `"2026-10-22T13:05:00Z"`, not a `datetime` | No error expected |
| Duplicate key, top level (criterion 2, AC-1.4) | `suite:` on lines 2 and 4 | rejected | `SuiteError` at `4:1` naming `suite` |
| Duplicate key, nested (criterion 2, AC-1.4) | `id:` twice inside `scenarios[0]`, second on line 6 | rejected | `SuiteError` at `6:5` naming `id` |
| Several duplicates | two different duplicated keys | all reported, in document order | one `SuiteError` with several violations |
| Keys compare as code points | `é` (one code point) and `e` + combining accent | two distinct keys, no error | documented, no normalization |
| Non-string key | `1: x`, `true: x`, `~: x`, `[a, b]: x` | rejected | `SuiteError` naming the key text and asking for a quoted string |
| Anchor (criterion 3, AC-1.5) | `defaults: &shared` on line 3, `*shared` later | rejected at the anchor, before any alias is reached | `SuiteError` at `3:11` naming `&shared` |
| Alias without anchor (criterion 3) | `other: *x` on line 2 | rejected at the alias, before PyYAML's "undefined alias" | `SuiteError` at `2:8` naming `*x` |
| Billion laughs (criterion 3, AC-1.5) | the nine-level fixture, first anchor `&a` on line 2 | rejected at `2:4`; `construct_document` never called; `tracemalloc` peak stays within a small fixed bound | `SuiteError` naming `&a` |
| Node flood without aliases | more than `MAX_YAML_NODES` nodes of flow collections | rejected at the node that crosses the limit, before construction | `SuiteError` naming the limit |
| Second document (criterion 4, AC-1.6) | `---` on line 3 after a complete first document; or content after `...` | rejected | `SuiteError` at the marker or content line, `a second YAML document starts here` |
| Leading `---` / trailing `...` only | `---\nversion: 1\n`, `a: 1\n...\n` | accepted (one document) | No error expected |
| Spine Suite seed (criterion 4) | the seed YAML with its comments | the expected dict: `version == 1` (int), booleans `True`, `equals == 1`, `expense_amount == 5000`, strings as written | No error expected |
| Native scalars (criterion 4) | `null`, `~`, `true`, `false`, `7`, `1.5`, `"7"`, `${VAR}` | `None`, `None`, `True`, `False`, `7`, `1.5`, `"7"`, `"${VAR}"` | No error expected |
| Scalar / list / empty top level | `just a string`, `- a`, `""`, `"# only a comment\n"`, `"---\n"` | rejected | `SuiteError` at the top-level node (or `1:1`) |
| Malformed YAML | unterminated flow sequence, tab indentation, unterminated quote, bad indentation, missing colon, a control character | rejected; no `yaml.*` exception escapes | `SuiteError` with PyYAML's problem text and the mark's line |
| Undecodable escape | `"\U0011FFFF"`, `"\UFFFFFFFF"`, `"\U00110000"` | rejected; PyYAML raises a bare `ValueError` or `OverflowError` here | `SuiteError`, no position |
| Lone surrogate | `"\uD800"`, `"\U0000D800"` as value or key | rejected | `SuiteError` at the scalar, `U+D800, a lone surrogate` |
| Byte order mark | `x<U+FEFF>y`, `"\uFEFF"`; a leading BOM | inner BOM rejected; leading BOM skipped | `SuiteError` at the scalar |
| Control characters via escape | `"\x00"`, `"\e"` | accepted as ordinary strings (decision pinned by a test) | No error expected |
| Nesting | `"[" * 10000`; `a: ` + 200 levels | the first rejected without `RecursionError`; the second loads | `SuiteError`, `the document nests too deeply` |
| Pure loader | the loader class | its MRO contains `yaml.composer.Composer` and `yaml.parser.Parser`, never `yaml.CSafeLoader`; the module source never names `CSafeLoader`, `cyaml`, or `yaml.load`; no other module under `src/agentproof` imports `yaml` | n/a |
| Ruff rules (retro item) | scratch `yaml.load(x)`, `eval`, `exec`, `pickle.loads`, `marshal.loads` under shell packages, and `pickle`, `marshal`, `shelve` imports under `loading` | `ruff check` fails with `S506`, `S307`, `S102`, `S301`, `S302`, and three `TID251`; the repository tree passes | n/a |

</frozen-after-approval>

## Code Map

- `packages/python/src/agentproof/loading/__init__.py` -- already exists (docstring only, from story 1.3); unchanged.
- `packages/python/src/agentproof/loading/yaml_safe.py` -- new; `_StrictLoader(yaml.SafeLoader)` overriding `compose_node` (alias, anchor, node count, tag check), `get_single_node` (second document, including after `...`), `construct_mapping` / `construct_sequence` (shape guard; duplicate and non-string keys, collected), `construct_scalar` (lone surrogate, inner U+FEFF), four checked scalar constructors and a timestamp-as-text constructor registered on the subclass; `_check_tag`, `_handle_remapped`, `_clip` / `_quote`, `_display_tag`, `_field` (1-based `line:column`), `_from_yaml_error`; `load(text, *, source)`; `__all__ = ["load"]`.
- `packages/python/src/agentproof/constants.py` -- `MAX_YAML_NODES = 200_000` with its rationale (the only change).
- `packages/python/tests/unit/loading/__init__.py` -- new; docstring only.
- `packages/python/tests/unit/loading/test_yaml_safe.py` -- new; one test per matrix row, each fixture-backed rejection asserting the exception type, `source`, the `line:column` field, and the key or tag named; `tracemalloc` bound and a `construct_document` tripwire for the billion-laughs case; MRO, source-text and whole-tree import scans for the pure loader and the single entry point; the spine seed and native scalars; the YAML 1.1 surprises and explicit-tag breadth pinned to the docstring; the 70-input nasty-text regression net that accepts only `dict` or `SuiteError` and never the generic fallback.
- `packages/python/tests/unit/test_tooling_config.py` -- two tests: the five S rules are selected and no `src/` per-file-ignore names an S rule; the only S ignore anywhere is `S301` on `test_errors_taxonomy.py`.
- `packages/python/tests/fixtures/yaml/` -- new; `custom-tag.yaml`, `python-object-tag.yaml`, `duplicate-key-top-level.yaml`, `duplicate-key-nested.yaml`, `anchor-alias.yaml`, `billion-laughs.yaml`, `multi-document.yaml`, `scalar-top-level.yaml`, `suite-seed.yaml`; all LF.
- `packages/python/pyproject.toml` -- `S102`, `S301`, `S302`, `S307`, `S506` added to `select`; `pickle`, `marshal`, `shelve` added to the TID251 banned-api list; `S301` ignored only on `tests/unit/test_errors_taxonomy.py`; `types-pyyaml` added to the dev group (stubs for `mypy --strict`; dev only, never in the wheel).
- `packages/python/uv.lock` -- regenerated by `uv sync` for the dev stub package.
- Existing to respect: AD-19 (size limits are enforced by `io.read_limited` before this function, so `load` takes text, not bytes or a path); `.importlinter` layers; the purity checker; `tests/unit/test_import_contracts.py`, whose `test_shell_package_is_exempt_from_both_guards` writes `socket` and `open` into `io/__init__.py` and expects ruff to pass (the new S rules do not fire on those names).

## Tasks & Acceptance

**Execution:**
- [x] `packages/python/src/agentproof/loading/yaml_safe.py` -- the loader subclass and `load` -- criteria 1 to 4
- [x] `packages/python/src/agentproof/constants.py` -- `MAX_YAML_NODES`
- [x] `packages/python/tests/fixtures/yaml/*.yaml` -- one fixture per rejection class plus the spine seed, LF -- criteria 1 to 4
- [x] `packages/python/tests/unit/loading/test_yaml_safe.py` -- every matrix row -- criteria 1 to 4
- [x] `packages/python/pyproject.toml`, `tests/unit/test_tooling_config.py` -- the five S rules, three module bans, one test ignore, the stub package; ruff proof on scratch files -- retro item
- [x] local verification -- `uv run check` green; `uv run --python 3.12 --locked --isolated pytest tests/unit/loading -q` green; caches removed

**Acceptance Criteria:**
- Given a document with `!!python/object` or any custom tag, when `yaml_safe.load(text, source=)` runs, then it raises `SuiteError` naming the source and line, and no object is constructed.
- Given a mapping with the same key twice at any level, when loaded, then it raises naming the key and the line of the second occurrence.
- Given a document using `&a` and `*a`, or the billion-laughs fixture, when loaded, then it raises before any expansion, naming the line.
- Given a stream with a second `---` document, when loaded, then it raises naming the line of the second marker; and the spine's Suite seed loads to a dict with string keys and native scalars.

## Implementation Notes

**2026-10-23, implementer (worktree `D:\AgentProof-wt-3-2`, branch `story/3-2-safe-yaml-loader`, baseline `fca6286`).** The first worktree was lost to an environment restart before anything was committed; this is the story rebuilt in one pass from origin/backlog with both earlier review rounds (eight findings, then G1 to G8) built in from the start. The notes below describe the result, not the history.

Decisions taken where the story left room:

- Probed PyYAML 6.0.3 before designing (libyaml is present locally, so `yaml.CSafeLoader` exists and the pure-loader tests are meaningful): the anchor's mark sits on the `&` and the alias's on the `*`; a tagged node's `start_mark` is the tag token, which lets the written handle be read back from the source text at `mark.index`; the second `DocumentStartEvent` is marked on the `---` line; `ReaderError` carries a character index, not a mark; the stock SafeLoader turns timestamps into `datetime`/`date`; stock PyYAML itself raises `ValueError`, `IndexError` or `KeyError` for `!!int x`, `!!int ''`, `0x_`, a 5000-digit integer, and `ConstructorError` for a plain `=`.
- The loader is `_StrictLoader(yaml.SafeLoader)`, module-private, so `load` stays the one entry point; `load` instantiates it directly (`get_single_node()` / `construct_document()` / `dispose()`, which is what `yaml.load` does internally), so the module never calls `yaml.load` or `safe_load` and ruff S506 cannot flag it. AGENTS.md says "`yaml.safe_load` only (the one `SafeLoader` subclass of ADR-019)"; the subclass is the ADR's rule.
- `compose_node` rejects, before calling PyYAML's composer: an `AliasEvent`, a `NodeEvent` with an anchor, then (counting every node on entry) the node that crosses `MAX_YAML_NODES`; after composition `_check_tag` rejects a resolved tag outside `_ALLOWED_TAGS`, a plain `=` (the YAML 1.1 value tag, which stock PyYAML also refuses, now with a message that says to quote it), and a tag that does not fit its node (`!!map` needs a `MappingNode`, `!!seq` a `SequenceNode`, everything else a `ScalarNode`). Composition finishes for the whole document before construction starts, so none of these constructs an object; tests pin that with a tripwire on `construct_document` and `construct_object`.
- The `%TAG` note compares only the handle the rejected tag was written with: `_TAG_START` reads the written tag at the node's start index (`!<verbatim>` has no handle; `!`, `!!`, `!name!` do), and the note is added only when `tag_handles[handle]` differs from `DEFAULT_TAGS[handle]`. A `%TAG` directive for some other handle adds nothing.
- `get_single_node` reports a second document at the `---` mark, and also content after an explicit `...`, where PyYAML's own message would have been `expected '<document start>'`; `a: 1\n...\n` alone is one document.
- `construct_mapping` is replaced entirely (so PyYAML's `flatten_mapping` merge logic never runs) and starts with an `isinstance(node, MappingNode)` guard, as does `construct_sequence`; non-scalar keys, non-string scalar keys and duplicates are recorded with their marks and raised together after construction, sorted by position. Non-string keys are rejected because the contract is `dict[str, JsonValue]`; this is one step stricter than the story's wording. Keys are compared as code points, no normalization (documented and pinned: NFC and NFD forms of a letter are two keys).
- `construct_scalar` (called for every string, key or value, however written) records a lone surrogate or a U+FEFF at the scalar's mark. PyYAML's reader checks only raw characters, so `"\uD800"` reaches the result as a `str` that fails `.encode("utf-8")` when a report is written. Decisions: surrogates and inner U+FEFF are rejected; a leading BOM is skipped by the scanner and accepted; control characters written as escapes (`"\x00"`, `"\e"`) are accepted as ordinary strings because JSON carries them and `.encode` accepts them (pinned by `test_control_characters_written_as_escapes_are_accepted_as_documented`).
- Four checked scalar constructors (`construct_int_checked`, `construct_float_checked`, `construct_bool_checked`, `construct_null_checked`) are registered on the subclass only (a test asserts the stock table is untouched). `!!null x`, which PyYAML silently reads as `None`, is rejected. Timestamps are kept as text via `construct_timestamp_text`.
- Explicit numeric tags are broader than plain scalars (PyYAML's constructors run without the resolver's pattern): `!!int` accepts non-ASCII decimal digits and sexagesimal text, `!!float 1e999` yields infinity, `!!timestamp` accepts any scalar. Documented in the module docstring and pinned by `test_explicit_numeric_tags_are_broader_than_plain_scalars`; the models reject non-finite numbers downstream.
- Messages: user text is passed through `_quote` = `repr(_clip(text))` (80 characters, then `...`), for tags, anchors, aliases, keys and typed-scalar payloads. `repr` already escapes U+202E, U+0085, U+200B, U+FEFF and control characters (probed: `repr('a\u202eb')` is `'a\u202eb'` with a literal backslash-u), so the reviewer's concern that bidi and NEL survive `!r` quoting did not reproduce; `test_bidirectional_and_control_characters_in_a_key_are_escaped_in_the_message` pins it, and no further fix was needed.
- `Violation.field` carries the 1-based `line:column` (`"6:5"`) because no field path exists before the document parses; `Violation.message` carries no position, so the CLI's `<kind>: <message> (<source>:<field>)` renders as `suite: duplicate key 'id' (agentproof.yaml:6:5)`. Routed to story 3.3, which mixes these with dotted model paths.
- `load` catches, in order: `SuiteError` (re-raised), `yaml.YAMLError` (mapped with its mark), `RecursionError` (`the document nests too deeply`), `(ValueError, OverflowError)` (`the document has a character escape that is not a valid Unicode character`; PyYAML calls `chr()` on `\U` escapes without a range check, `ValueError` above U+10FFFF and `OverflowError` for `\UFFFFFFFF` on CPython 3.12), and finally `Exception`, mapped to `the document could not be parsed (<ExceptionType>)` naming only the type, because an exception's text may echo the input. The fallback is defense in depth: the nasty-input test refuses to accept it, so a gap shows up as a failing test instead of a quiet pass.
- Ruff: `select` gained `S102`, `S301`, `S302`, `S307`, `S506` for every file; the TID251 banned-api list gained the `pickle`, `marshal`, `shelve` modules (core packages only; the shell packages keep their TID251 exemption); `tests/unit/test_errors_taxonomy.py` is the single `S301` ignore, with a comment, because it deliberately round-trips an `InputError` through `pickle.loads`. No per-file-ignore under `src` names an S rule (tested). `types-pyyaml>=6.0.12` was added to the dev group (PyYAML ships no stubs and `mypy --strict` runs on `src`); runtime dependencies are unchanged.

Observed (commands run in this session):

- `uv sync` (uv 0.13.5) on CPython 3.13.16; `types-pyyaml==6.0.12.20260906` installed.
- Fixture files: 0 carriage returns in each of the nine files at write time (written LF through the Write tool).
- `uv run check` from `packages/python`, exit 0: `==> ruff check` `All checks passed!` (purity checker silent), `==> ruff format --check` `49 files already formatted`, `==> mypy --strict` `Success: no issues found in 24 source files`, `==> lint-imports` `Contracts: 7 kept, 0 broken.`, `==> pytest` `964 passed in 58.29s` (the whole suite on the current backlog; this story contributes 205 tests in `test_yaml_safe.py` and 2 in `test_tooling_config.py`). The gate was rerun after the final code change (the `OverflowError` fix) with the same result: exit 0, `964 passed in 78.71s`.
- `uv run --python 3.12 --locked --isolated pytest tests/unit/loading tests/unit/test_tooling_config.py -q -p no:cacheprovider` -> `209 passed` on CPython 3.12. The first 3.12 run failed two `\UFFFFFFFF` cases (`OverflowError` instead of `ValueError`, caught by the nasty-input test refusing the generic fallback); fixed by catching `OverflowError` with `ValueError`.
- Fuzz (scratch script, not committed): 60,000 random mutations of 40 tricky seeds (indicator characters, escapes, surrogates, BOMs, tags, directives, numeric edge cases), run on CPython 3.12 and 3.13: 0 exceptions other than `SuiteError`, 0 uses of the generic fallback.
- Ruff proof, scratch files `src/agentproof/cli/_scratch_eval.py` (exec, marshal, pickle, eval) and `src/agentproof/io/_scratch_yaml_load.py` (yaml.load), both TID251-exempt shell packages, plus `src/agentproof/loading/_scratch_modules.py` importing the three modules, `uv run ruff check src --output-format concise` exit 1:
  `src\agentproof\cli\_scratch_eval.py:8:5: S102 Use of `exec` detected`
  `src\agentproof\cli\_scratch_eval.py:9:5: S302 Deserialization with the `marshal` module is possibly dangerous`
  `src\agentproof\cli\_scratch_eval.py:10:5: S301 `pickle` and modules that wrap it can be unsafe when used to deserialize untrusted data, possible security issue`
  `src\agentproof\cli\_scratch_eval.py:11:12: S307 Use of possibly insecure function; consider using `ast.literal_eval``
  `src\agentproof\io\_scratch_yaml_load.py:7:12: S506 Probable use of unsafe `yaml.load`. Allows instantiation of arbitrary objects. Consider `yaml.safe_load`.`
  `src\agentproof\loading\_scratch_modules.py:3:8: TID251 `marshal` is banned: marshal deserializes code objects (AD-19); artifacts are JSON and YAML only`
  `src\agentproof\loading\_scratch_modules.py:4:8: TID251 `pickle` is banned: pickle deserializes arbitrary objects (AD-19); artifacts are JSON and YAML only`
  `src\agentproof\loading\_scratch_modules.py:5:8: TID251 `shelve` is banned: shelve is pickle-backed (AD-19); artifacts are JSON and YAML only`
  `Found 8 errors.` All three scratch files deleted (0 `_scratch_*` files remain); `ruff check .` then `All checks passed!`.
- Measurements, on the development machine (CPython 3.13, Windows; wall time without `tracemalloc`, peak from a second run with it; wall times varied by up to 2x between runs because the machine was shared, the stock pure `SafeLoader` baseline moved from 2.8 s to 6.9 s on the same 0.81 MB text, so read them as ranges; peaks were identical across runs):

  | Document | Nodes | Wall time | `tracemalloc` peak | Outcome |
  | --- | --- | --- | --- | --- |
  | billion-laughs fixture | n/a | 0.003 s | 11,461 bytes (8,229 in the first session) | rejected at `&a`, 2:4 |
  | 0.81 MB flat `key: value` lines | about 58,000 | 2.5 to 10.7 s (stock pure `SafeLoader`: 2.8 to 6.9 s) | 37.4 MB | loads |
  | 4.29 MB small flow mappings, one per line | more than 200,000 | 9.5 to 20.8 s | 108.0 MB | rejected at node 200,001, line 22,223 |
  | 2.86 MB flat sequence | about 176,000 | 9.5 to 12.9 s | 102.3 MB | loads |

  Without the node bound the same 4.4 MB flow-mapping file took 246 s and 829 MB in the reviewer's run. The loader has no quadratic path (duplicate-key tracking is a dict lookup, violation sorting runs once at the end) and runs at parity with the stock pure `SafeLoader`; the cost is PyYAML's pure-Python parser. `MAX_YAML_NODES = 200_000` therefore bounds the worst alias-free document under `MAX_SUITE_BYTES` to about 10 to 20 s and about 108 MB here; 100,000 would halve both and reject the 2.86 MB sequence. The real-limit test (`test_the_real_node_limit_rejects_a_large_alias_free_document`) takes 6 to 26 s depending on load and is the slowest test in the suite.

Risks and open points:

- AD-19's sentence "`pickle`, `marshal`, `eval`, `exec`, and `yaml.load` without the safe loader are banned by the ruff list in AD-1" was not true at baseline and is now true through two mechanisms: flake8-bandit rules S102/S301/S302/S307/S506 for every file, plus TID251 module bans for `pickle`, `marshal`, `shelve` that apply only to the core packages. The spine should say so (wording in the PR description). AD-19 should also mention `MAX_YAML_NODES` beside the byte limits.
- `tests/fixtures/yaml/**` is not pinned to LF in `.gitattributes` (only `tests/golden/**` and `schemas/*.json` are); `* text=auto` normalizes them in the index, and line numbers do not depend on the line ending, but a one-line rule would make the guarantee explicit. Not changed (outside the Code Map).
- `Violation.field` as `line:column` is a convention story 3.3 inherits.
- Rejecting non-string keys, the merge key, `=`, surrogates and inner U+FEFF is stricter than the story's four rejections; each is a few lines to relax.
- Escaped control characters (NUL, ESC) are accepted; if the models or the HTML renderer need them rejected, that is a one-line extension of `_FORBIDDEN_CHARS`.
- The nesting guard and the escape handler report no position (`field=""`) because the exceptions carry none. The real recursion boundary on CPython 3.12 and 3.13 is between 200 and 400 levels (`a: ` + 200 levels loads, 400 is rejected); 3.14 and 3.15 are covered by CI, not tested locally.
- The generic `except Exception` fallback could mask a bug in this module as an input fault; the nasty-input test rejects any use of it, which is the guard.

## Plan Change Log

- 2026-10-23: the story was rebuilt after the first worktree was lost, with the first review round (eight findings) and the second (G1 to G8) applied in one pass. Relative to the first plan: `constants.py` and `tests/unit/test_tooling_config.py` joined the Code Map; the matrix gained the tag-shape, typed-scalar, `%TAG`, node-limit, surrogate, BOM, escape and nesting rows; the "well under a second" performance sentence was replaced by measured numbers.

## Review Triage Log

### Review round 1 (coordinator triage), 2026-10-23

Eight findings; seven built in, one routed.

| # | Finding | Disposition | Evidence |
| --- | --- | --- | --- |
| 1 | `construct_mapping` dropped PyYAML's `MappingNode` guard and `!!map` is allowed, so `!!map 5` / `!!map ab` / `!!map [x, y]` raised `ValueError`/`TypeError` | built in | compose-time shape check in `_check_tag`; guards first in `construct_mapping` and `construct_sequence`; four checked scalar constructors for the stock-PyYAML escapes found while probing (`!!int x`, `!!int ''`, `!!bool x`, `0x_`, `0b_`, 5000-digit ints); `test_a_tag_that_does_not_fit_its_node_is_rejected_before_construction`, `test_constructors_guard_their_own_node_shape`, `test_a_typed_scalar_the_constructor_cannot_read_is_rejected`, `test_a_huge_integer_literal_is_rejected_not_an_escaped_value_error`, `test_any_text_either_loads_to_a_dict_or_raises_suite_error` |
| 2 | Alias-free resource exhaustion: 4.4 MB flow mappings 246 s / 829 MB; suspected O(n^2) | built in (bound); no quadratic path found | `MAX_YAML_NODES = 200_000` counted in `compose_node`; measurements above; `test_the_node_limit_comes_from_constants`, `test_a_document_at_the_node_limit_loads`, `test_a_document_over_the_node_limit_is_rejected_naming_the_limit`, `test_the_real_node_limit_rejects_a_large_alias_free_document` |
| 3 | "Only YAML entry point" not checked mechanically | built in | `test_yaml_safe_is_the_only_module_that_imports_pyyaml` |
| 4 | Content after `...` got PyYAML's `expected '<document start>'` text | built in | `get_single_node` maps that `ParserError` to the second-document message at its mark; `test_content_after_an_explicit_document_end_is_a_second_document`, `test_an_explicit_document_end_alone_is_one_document` |
| 5 | Message shows text the user never wrote after `%TAG` rebinding | built in (refined by G4) | docstring says "resolved tag"; note added only when the used handle was remapped |
| 6 | YAML 1.1 scalar surprises undocumented | built in | docstring list verified against the stock loader; `test_yaml_1_1_scalar_surprises_are_as_the_module_docstring_lists`, `test_a_yaml_1_2_directive_is_accepted_but_1_1_rules_still_apply`, `test_a_yaml_2_directive_is_rejected` |
| 7 | `Violation.field` carries `line:column`, not a field path | routed to story 3.3 by the orchestrator | no change |
| 8 | Ruff rules and tests: S rules for the whole package, no S ignore under `src`, scratch-file proof, `types-pyyaml` dev-only | built in | `pyproject.toml`; `test_unsafe_deserialization_rules_are_selected_and_never_ignored_under_src`, `test_the_only_s_rule_ignore_is_the_pickle_round_trip_test`; proof output above |

### Review round 2 (coordinator triage), 2026-10-23

| # | Finding | Disposition | Evidence |
| --- | --- | --- | --- |
| G1 | `\U` escape above U+10FFFF raised a bare `ValueError` out of `load` | built in, and widened | `except (ValueError, OverflowError)` in `load` (CPython 3.12 raises `OverflowError` for `\UFFFFFFFF`, found by the 3.12 run); all three inputs in `test_a_unicode_escape_above_the_last_code_point_is_a_suite_error` and in the nasty-input list |
| G2 | Lone surrogates via escape (`"\uD800"`, `"\U0000D800"`) and control characters via escape pass through | surrogates rejected; control characters accepted by decision | `construct_scalar` check; `test_a_lone_surrogate_written_as_an_escape_is_rejected_in_keys_and_values`, `test_every_surrogate_in_the_document_is_reported_in_order`, `test_a_surrogate_pair_written_as_one_astral_escape_is_fine`, `test_control_characters_written_as_escapes_are_accepted_as_documented` |
| G3 | No length cap on echoed user text; bidi and NEL possibly surviving `!r` | built in; bidi concern did not reproduce | `_clip`/`_quote`; `test_user_text_echoed_in_a_message_is_clipped_to_eighty_characters`, `test_a_short_value_is_echoed_whole`, `test_a_very_long_duplicate_key_is_clipped_in_the_message`, `test_bidirectional_and_control_characters_in_a_key_are_escaped_in_the_message` (repr escapes U+202E, U+0085, U+200B, U+001B) |
| G4 | `%TAG` note fired whenever any directive was present | built in | `_handle_remapped` compares only the handle used; `test_tag_directive_for_another_handle_adds_no_resolution_note`, `test_verbatim_tag_has_no_handle_and_no_resolution_note`, `test_tag_written_with_a_remapped_named_handle_is_reported_as_resolved`, `test_tag_written_with_a_remapped_primary_handle_is_reported_as_resolved` |
| G5 | Duplicate-key detection does no Unicode normalization | documented, behavior unchanged | docstring paragraph; `test_keys_are_compared_as_code_points_with_no_normalization` |
| G6 | Stray U+FEFF mid-document accepted | rejected (leading BOM still skipped) | `construct_scalar` check; `test_a_byte_order_mark_inside_the_document_is_rejected`, `test_a_leading_byte_order_mark_is_skipped` |
| G7 | Explicit numeric tags accept more than plain scalars | documented | docstring paragraph; `test_explicit_numeric_tags_are_broader_than_plain_scalars` |
| G8 | Nesting test used a depth far past the real boundary | built in | `test_reasonable_nesting_loads_and_the_node_limit_does_not_fire_first` (200 levels) beside `test_pathological_nesting_is_a_suite_error_not_a_recursion_error` |

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: gate green, `lint-imports` 7 kept, purity clean on `loading`
- `cd packages/python && uv run pytest tests/unit/loading -q` -- expected: every test passes
- `cd packages/python && uv run --python 3.12 --locked --isolated pytest tests/unit/loading -q` -- expected: every test passes on the lowest CI version
- `git status --short` -- expected: only the Code Map paths and this plan

**Manual checks (if no CLI):**
- `git status` shows only the Code Map paths.
