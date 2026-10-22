# Golden files

Files under this directory are expected artifacts (reports, comparisons, canonical
JSON) that tests compare against freshly produced output **byte for byte** (architecture
AD-17). A single carriage return would make such a comparison fail on one platform and
pass on another, so the repository's `.gitattributes` pins `**/tests/golden/**` to LF
line endings on every checkout, whatever `core.autocrlf` is set to.

Rules:

- Never hand-edit a golden file on Windows with an editor that rewrites line endings;
  `.editorconfig` asks editors for LF, and `tests/unit/test_repo_hygiene.py` fails if any
  file here contains a `\r`.
- Regenerate a golden file from the code that produces it and review the diff; a golden
  file is a claim about behavior, not a fixture to be patched.
- Keep the directory flat per artifact kind (`reports/`, `comparisons/`, ...) once the
  first golden tests arrive (epic 3 and later).

This README is itself the first LF-protected file and is what the hygiene test reads
until real golden artifacts exist.
