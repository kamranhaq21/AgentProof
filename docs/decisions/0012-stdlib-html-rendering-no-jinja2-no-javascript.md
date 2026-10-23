# ADR-012 (AD-12): Stdlib HTML rendering, no Jinja2, no JavaScript

**Status:** Accepted.
**Decision.** String templates with `html.escape(quote=True)`, `<details>` collapsing, CSP meta, evidence-referenced events always expanded, then the first 500 collapsed, the rest counted.
