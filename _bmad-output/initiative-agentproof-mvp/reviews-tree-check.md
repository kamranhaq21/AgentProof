# Tree and Dependencies check — AgentProof v0.1

Checked 2026-10-22 against `validate-checks.md` sections Tree and Dependencies. Inputs: the initiative file, its `tickets.toml`, the eleven epic files and their `tickets.toml`, the story files' `Files:` lines for epics 1 to 9, the four `sources:` and two `companions:` files (existence and id grep only), and `tickets.py status` / `next` on the initiative.

## Verdict

The tree is sound at the initiative-to-epic level: all 31 requirements and 10 constraints are covered by at least one epic, every epic `covers` id and every Requirements-line parent id resolves to the initiative, every `sources:` and `companions:` file exists and every cited FR/AC/NFR/AD/ADR/OQ/UJ/SM id and spec section is present, the initiative `tickets.toml` lists the eleven epics in the user's fixed order with real needs on each `after`, it opens with a platform-baseline epic, and `tickets.py status` reports no cycle, `order_conflict`, `unpinned_after`, or `undeclared_after`. The problems are at the Dependencies level: five entry-level `after` gaps let items without a dependency path touch the same file or depend on something not yet built (the runner story runs the example before `tool_call_count` exists; epic 1 story 5's hygiene files, including the LF rule the golden tests rely on, are upstream of nothing; `loading/report.py` has two conditional owners across epics 6 and 7; `cli/app.py` and `__init__.py` are edited by parallel stories in epic 3; `ci.yml` is edited by parallel stories across epics 1, 5, 8, and 9). None of these needs a new story; each is an `after` edit or an ownership line. Three coverage bookkeeping items (epic 6 omits R18 and R23 from `covers` although its R5 builds them; epic 3 cites R19 without covering it; epics 4 and 5 cover C3/C4/C5 without a Requirements line) should be fixed before the set-level validation so entry `covers` resolve cleanly.

## Coverage table

| Initiative id | Covered by epics | Gap? |
|---|---|---|
| R1 | 3 | no |
| R2 | 3 | no |
| R3 | 2 | no |
| R4 | 5 | no |
| R5 | 4 | no |
| R6 | 5 | no |
| R7 | 2 (config models, union), 4 (evaluators) | no; split stated in each epic's Requirements and in C4 |
| R8 | 4 | no |
| R9 | 4 | no |
| R10 | 4 | no |
| R11 | 5 | no |
| R12 | 4 | no |
| R13 | 4 (protocol, Fixture Agent, conformance), 11 (real Adapter, gated) | no |
| R14 | 2 (Report model), 6 (writer, embedding) | no |
| R15 | 6 | no |
| R16 | 7 | no |
| R17 | 3 (codes 2 and 4, one-line errors), 4 (0, 1, 3, matrix test) | no |
| R18 | 3 only | partial: the command set spans epics 3, 4, 5, 6, 7 and the temp-then-rename clause is epic 5 story 3; epic 6 R5 cites R18 but epic 6 `covers` omits it (F3) |
| R19 | 5 (`redact`); epic 3 R5 cites it for `scrub_text` but epic 3 `covers` omits it | bookkeeping gap (F3) |
| R20 | 8 | no |
| R21 | 9 | no |
| R22 | 4 (initial `__all__`); later names added by 5.2, 5.4, 6.1, 6.2, 7.1, 7.2 | no owner of the final "exactly AD-15" check (F10) |
| R23 | 9 (documented deferred), 10 (viewer gate); the `junit` exit-2 rejection is built by epic 6 R5 / 6.3 without R23 in epic 6 `covers` | bookkeeping gap (F3) |
| R24 | 2 (`dumps` byte identity), 6 (golden files) | no |
| R25 | 3 (YAML, size limit), 9 (hardening tests) | no |
| R26 | 5 | no |
| R27 | 1 (matrix, four dependencies), 9 (`pip-audit` restated) | overlap: `pip-audit` is built by 1.6 and restated by epic 9 R3 (F11) |
| R28 | 1 (version source, 0.x policy), 2 (Schema Versions, drift test) | no |
| R29 | 1 (CI stages), 8 (§12.4 e2e chain); per-feature test clauses delivered under R7/R17/R19/R25 in epics 3, 4, 5 | no, but the split is unstated in the initiative (F12) |
| R30 | 4 (evaluation time), 6 (HTML size) | no |
| R31 | 5 | no |
| C1 | 1 | no |
| C2 | 2 | no |
| C3 | 3 (exit-code module, `app.py` exits), 4, 7 | epic 4 has no Requirements line naming C3 (F4) |
| C4 | 2, 4 | epic 4 has no Requirements line naming C4 (F4) |
| C5 | 4, 5 | epic 5 has no Requirements line naming C5 (F4) |
| C6 | 2, 3, 5, 6, 7 | no; each cites a different AD |
| C7 | 1 | no |
| C8 | 9 (SECURITY.md); epic 11 Boundaries enforce the one-Adapter rule | no |
| C9 | 1 (provisional name, no LICENSE), 9 (release gate) | no |
| C10 | 1, 9 | no |

No initiative Notes deferral is needed; nothing is uncovered.

## Findings

- **[fix]** Runner story runs the example before `tool_call_count` exists (epic-04 `tickets.toml` entry 7) — `after = [1, 5, 6, "3.5", "3.6"]` omits entry 4. The example Suite is the spine seed (epic 3 story 6), which carries `tool_not_called-0`, `tool_call_count-1`, and `final_output_contains`; story 7's verify runs that Suite, so it needs the `tool_call_count` evaluator from story 4, and 4.3's key-set test against the models union cannot pass until 4.4 and 4.5 both land — Change 4.7 to `after = [1, 4, 5, 6, "3.5", "3.6"]`.
- **[fix]** Epic 1 story 5 is upstream of nothing, so the LF rule and hygiene files it owns are not built before the items that rely on them (epic-01 `tickets.toml` entries 4 and 5; epic-02 entry 1; epic-06 entry 4; epic-09 entry 4) — 1.5 (`.gitattributes` LF for `tests/golden/**`, `CONTRIBUTING.md`, `SECURITY.md`, `docs/decisions/*.md`) is `after = [1]` and only 1.7 waits on it. 2.1's verify ("byte for byte on Linux and Windows CI") and 6.4 ("verifies `.gitattributes` keeps them LF") need the LF rule; 1.4 and 1.5 both write `CONTRIBUTING.md` with no path between them (1.4's Files line already says "written here if story 5 has not landed"); 9.4 rewrites `SECURITY.md` and `CONTRIBUTING.md` that 1.5 created with no path. — One edit resolves all of it: 1.4 `after = [2, 5]`, and drop the conditional clause from 1.4's Files line. (Alternative: 2.1 `after = ["1.3", "1.4", "1.5"]` and 1.4 keeps the conditional.)
- **[fix]** Epic 6 `covers` omits R18 and R23 although its R5 builds the `report` command and the `junit` exit-2 rejection; epic 3 R5 cites R19 without covering it (epic-06 file frontmatter and R5; epic-03 file frontmatter and R5) — A child's `covers` must resolve through the Requirements line to a parent id, and the Requirements line must name a parent id the epic covers. — Add `"R18", "R23"` to epic 6 `covers` and cite R23 on its R5; add `"R19"` to epic 3 `covers` (its part: `scrub_text` and the console filter) or drop "initiative R19" from epic 3 R5 and leave R19 to epic 5. Then add a sentence to initiative R18 or its Notes saying epic 3 owns the command-set contract and epics 4 to 7 each add their commands under R17/R11/R15/R16, and epic 5 story 3 owns the temp-then-rename clause.
- **[fix]** `loading/report.py` (`parse_report`, `load_report`) has two conditional owners with no dependency path (epic-06 entry 3 Files line; epic-07 entry 1; initiative `tickets.toml` epic 7 `after` needs line; epic-07 file R1) — 6.3 (`after = [2]`) and 7.1 (`after = ["6.1"]`) are parallel; 6.3 says "if epic 7 story 1 has not landed, otherwise reuse", 7.1 says "if epic 6 story 3 already created it, this story completes it", and the initiative's epic 7 `after` says epic 6 provides `parse_report` while epic 7 R1 says epic 7 builds it. 7.1 and 6.2 also both edit `src/agentproof/__init__.py` with no path. — Give it one home in epic 6: either insert the `parse_report`/`load_report` story before 6.3 in epic 6 (6.3 and 7.1 wait on it; 7.1 shrinks to the version-dispatch upgrade stub or is dropped and epic 7 R1 cites epic 6), or move 6.3's `report` command to run with the minimal loader it owns and set 7.1 `after = ["6.3"]`. Update epic 7 R1 and the initiative `after` needs line to match whichever is chosen.
- **[fix]** Parallel stories in epic 3 edit `cli/app.py` and `__init__.py` (epic-03 `tickets.toml` entries 1, 3, 5) — 3.1 creates `cli/app.py` and `__init__.py`; 3.3 (`after = [2, "2.2"]`) adds the violation formatter to `cli/app.py` and exports to `__init__.py`; 3.5 (`after = [1]`) adds global options to `cli/app.py`. 3.1 and 3.3 have no path; 3.3 and 3.5 have no path. — 3.3 `after = [1, 2, "2.2"]`; 3.5 `after = [3]` (or move the `--verbose`/`--no-color` options into 3.1, which already owns the app, and leave 3.5 with `redaction/apply.py` and `io/console.py` only).
- **[suggest]** `.github/workflows/ci.yml` is edited by stories with no dependency path (epic-01 entry 6; epic-05 entry 5; epic-08 entry 3; epic-09 entry 1) — 1.6 (build/smoke/audit jobs), 5.5 (networkless step), 8.3 (e2e job), 9.1 (docs job) each add a job; 5.5 has no path to 1.6, 8.3, or 9.1 (6.1 waits on 5.3 and 5.4, not 5.5). Epic-level order makes this safe only if epics are built strictly in sequence, which `next` does not enforce (it shows 5.1 ready today). — Pin 5.5 `after = [4, "1.6"]` and 8.3 `after = [1, "5.5", "7.3"]`, or record a Decision in epic 5 Notes that separate jobs in `ci.yml` are not a shared edit.
- **[suggest]** `pyproject.toml` and `assertions/registry.py` are edited by parallel stories (epic-03 entry 6 and epic-04 entry 6; epic-04 entries 4 and 5) — 3.6 (package data) and 4.6 (entry-point group) have no path; 4.4 and 4.5 both do a "registry update" with no path. — 4.6 `after = [2, "3.6"]`; 4.5 `after = [4]`, or have each evaluator module register itself so 4.4 and 4.5 stop touching `registry.py`.
- **[suggest]** Epic 9 story 3 hardening cases overlap epic 5 story 3's verify (epic-09 entry 3; epic-05 entry 3) — Both test a locked target on Windows and a symlink escaping the Output Directory ending in exit 3. — State the split: 5.3 owns the guard and its unit tests; 9.3 owns the CLI-level integration tests across all five cases, and say so in 9.3's description.
- **[suggest]** Two tag-triggered release workflows with no stated relation (epic-01 entry 6 Files line `release-draft.yml`; epic-09 entry 5 Files line `release.yml`) — 1.6 attaches the wheel to a draft release on a tag; 9.5 publishes on a tag with trusted publishing. Both sides should say 9.5 extends or replaces `release-draft.yml`. — Add to 9.5's description "replaces the draft-only workflow from epic 1 story 6" and to 1.6's a note that epic 9 story 5 supersedes it.
- **[suggest]** No owner of the final "public API is exactly the AD-15 names" check (epic-04 file R7; epic-04 entry 8; initiative R22) — 4.8 asserts `__all__` holds "the names that now exist"; 5.2, 5.4, 6.1, 6.2, 7.1, 7.2 add names afterwards. — Name the owner of the equality test against the full AD-15 list (8.3 or 9.1 are the natural places) in that entry's description and in epic 4 R7 as a handoff.
- **[suggest]** `pip-audit` appears in epic 9 R3 and 9.3 although 1.6 builds it (epic-09 file R3; epic-09 entry 3) — Unexplained overlap on R27. — Drop "`pip-audit` runs in CI" from epic 9 R3 and the "remains a required CI job" clause from 9.3, or reword as "verifies the 1.6 job is still required on `main`".
- **[suggest]** Shared parent ids whose split is stated only in the epics, not the initiative (initiative Requirements R18, R29; Notes) — R29's per-feature test clauses are delivered under R7/R17/R19/R25 by epics 3, 4, 5, with epics 1 and 8 covering CI stages and the e2e chain. — Add one Notes line to the initiative recording the R18 and R29 splits so the Tree check does not depend on reading every epic.
- **[suggest]** Epic frontmatter `sources:` lists only the initiative while Requirements and References cite PRD AC ids, spine AD ids, and spec sections directly (all eleven epic files; e.g. epic 4 R3 "PRD AC-11.1 to AC-16.3", epic 3 R5 "initiative R19", epic 9 R4 "spec §11.1") — The check wants every source id on a Requirements line to exist in a `sources:` file; today they resolve only through the initiative's `sources:`. The tool does not flag it. — Either add the PRD and spine to each epic's `sources:` (they are cited in every References section) or keep Requirements lines to parent ids only and leave spine/PRD ids to Constraints and References.
- **[suggest]** Entry-level handoffs are stated on one side only for two human gates (epic-05 entry 1; epic-11 entry 1; epic-01 entry 6; epic-08 entry 1) — 5.1 does not say epic 11's spike reads `interviews.md`, and 1.6 does not say epic 8's workflow installs from its wheel job; the consuming side and the epic files do say so. — Add "read by epic 11 story 1" to 5.1's description and "consumed by epic 8 story 1" to 1.6's.
- **[suggest]** 8.2 edits `constants.py` "if not already present" (epic-08 entry 2 Files line; epic-02 entry 1) — 2.1 owns `constants.STATEMENTS` but does not enumerate the keys, so a later story may add one. — List the AD-20 statement keys (`compare_is_saved_data`, `artifacts_visible_to_readers`, the Redaction and Capture wordings, the §5 limits) in 2.1's description and drop the conditional from 8.2.
- **[ask]** 9.2's `docs/*.md` glob includes `docs/integrations.md` owned by 8.2 with no path (epic-09 entry 2 Files line; epic-08 entry 2) — Probably the six named pages only. — Confirm and name them explicitly in 9.2's Files line.
- **[ask]** Every epic file carries `after: []` while the initiative `tickets.toml` holds the real `after` (all eleven epic files, line 8) — `tickets.py status` reports no drift, so the toml is authoritative; confirm that is the convention and the frontmatter field is intentionally unused, or mirror the toml into the frontmatter.

## Confirmed

- All four `sources:` files and both `companions:` files exist at the stated paths; PRD FR-1 to FR-35, every AC-n.m cited (AC-11.1 to AC-16.3, AC-21.4, AC-21.5), NFR-1 to NFR-10, UJ-1 to UJ-4, SM-1 to SM-3, SM-C3, OQ-1 to OQ-15, H1 to H4, §5, §6.2, §8 exist in the PRD; AD-1 to AD-20, ARCH-1 to ARCH-7, Structural Seed, Capability map, Deferred exist in the spine; ADR-001 to ADR-020 and "Decisions explicitly not made" exist in the ADR log; spec §5.1, 6.8, 6.10, 8, 9, 11, 11.1, 12, 12.4, 13, 13.2, 13.3, 14.1, 19 exist; addendum section A and assessment section 4 exist; `AGENTS.md` exists.
- Every R1 to R31 and C1 to C10 is in at least one epic's `covers`; every epic `covers` id exists in the initiative; every epic Requirements line cites a parent id (R or C) that exists in the initiative; every epic entry's `covers` resolves to a Requirements line in its epic, and every epic Requirements line has at least one entry.
- The initiative `tickets.toml` lists epics only (no leaf in `tickets/`), in the user's fixed order, opens with the platform-baseline epic 1, and every epic-level `after` names a real need (epic 2 needs epic 1's layout and CI; 3 needs 2's models; 4 needs 3's CLI and 2's models; 5 needs 4's pipeline; 6 needs 5's pipeline and writer; 7 needs 6's Report output; 8 needs 7, 6, and 1's wheel job; 9 needs 8 and 5; 10 needs 6; 11 needs 5 and 4). `tickets.py status`: 61 tickets, all backlog, no cycle, `order_conflict`, `unpinned_after`, or `undeclared_after`; `next` shows 1.1 and 5.1 ready, matching the initiative's assumption that the interview gate is independent of epics 1 to 4.
- Every cross-epic `after` string points at an entry that exists: 2.1→1.3, 1.4; 3.1, 3.2→2.1; 3.3→2.2; 3.6→2.3; 4.1→2.4; 4.2→2.3, 3.1, 3.3; 4.7→3.5, 3.6; 5.2→4.7; 6.1→5.3, 5.4; 7.1→6.1; 8.1→1.6, 6.3; 8.3→7.3; 9.1→8.3; 9.3→5.3; 10.1→6.4; 11.1→5.1; 11.2→4.6, 5.2. Each is consistent with its epic's epic-level `after`.
- Shared setup has one home with the earliest owner upstream: `constants`, `errors`, Canonical serializer and `VOLATILE_PATHS` in 2.1 (the opening entry of epic 2); `read_limited` in 3.3; `write_atomic` and `io.paths` in 5.3; `scrub_text` in 3.5 and `redact` in 5.2 side by side in `redaction/` per AD-10 and the initiative Decision; `parse_trace` in 4.2 per the initiative Decision; `tests/helpers/adapters.py` created by 4.6 and extended by 5.6; `tests/unit/test_workflow_pins.py` created by 1.4 and extended by 1.6 and 8.1; `tests/golden/` opened by 2.1; `tests/conftest.py` guard owned by 5.5 with the `allow_subprocess` marker retrofit stated.
- Handoffs stated on both sides: epic 4 R5, Boundaries, and 4.7 leave a named identity `redact` step that epic 5 R2 and 5.2 replace; epic 5 R4, Boundaries, and 5.4 print a summary and reserve `replay-<id>.report.json` that epic 6 Notes and 6.1 turn into a file; epic 3's hand-written fixture Traces (Notes) are read by epic 4's Fixture Agent (R4); epic 4's conformance check and `RunContext` are consumed by epic 11 (Boundaries, 11.2, 11.3); epic 6's Report schema v1 gates epic 10 (10.1→6.4); epic 8's integrations page is executed by epic 9's docs test (epic 8 Done when, epic 9 R2); epic 1's provisional name and epic 9's release gate on OQ-1/OQ-2 are recorded on both sides.
- Every written epic file has Outcome, Done when with a production-delivery line, Boundaries, `covers`, and References; epics 10 and 11 are `refined: false` with a gating `unknown` on their first entry and no Requirements, as the initiative's Assumption says.
- Every unit the PRD (§4.1 to §4.10) and spec (§6.8, §6.10) touch is an epic or a named touch point with an owner (PyPI: epic 1 and 9; GitHub Actions: epic 1 CI and epic 8 example; Docker on the CI runner: epic 5; `schemas/`: epic 2; `examples/expense-agent/`: epic 3; entry-point group: epic 4; PROJECT_SPEC.md and AGENTS.md: never rewritten by a story).
- No file collisions among parallel stories in epics 2, 7, and 8, nor between epics 5 story 5 and 6, nor between 9.3 and any epic 5 to 8 story.
