"""The JSON Schemas of the serialized models, as pure functions (architecture AD-4; ADR-004).

The published contract for a Suite, a Trace, and a Report is the Pydantic model itself:
``schema_for`` returns ``model_json_schema()`` (JSON Schema draft 2020-12) with the
``$schema`` and an ``$id`` naming ``<kind>-v<version>``, and ``render`` returns it in
Canonical form (``canonical.dumps``: sorted keys, two-space indent, LF, one trailing
newline). Nothing here touches a file. The writer is the development-time script
``python -m agentproof_devtools.export_schemas`` in the devtools workspace member, which
never ships in the product wheel; ``tests/unit/test_schema_drift.py`` regenerates every
schema and fails on any difference from the committed file under the repository's
``schemas/``, so those files are never edited by hand and a schema that looks wrong is
fixed in the model. Consumers on other stacks validate against the files; the Python
package validates with Pydantic and never imports ``jsonschema`` (AD-16).
"""

from typing import Final

from pydantic import BaseModel

from agentproof.constants import SUPPORTED_VERSIONS
from agentproof.models import canonical
from agentproof.models.common import JsonValue
from agentproof.models.report import Report
from agentproof.models.suite import Suite
from agentproof.models.trace import Trace

__all__ = [
    "KINDS",
    "SCHEMA_URI",
    "file_name",
    "render",
    "schema_for",
    "schema_id",
    "schema_version",
]

SCHEMA_URI: Final = "https://json-schema.org/draft/2020-12/schema"
"""The JSON Schema dialect every exported schema declares (AD-4)."""

KINDS: Final[dict[str, type[BaseModel]]] = {"suite": Suite, "trace": Trace, "report": Report}
"""The artifact kinds that have a published schema, keyed as ``SUPPORTED_VERSIONS`` keys them."""


def schema_version(kind: str) -> int:
    """The schema version the exported file describes: the newest one the model accepts."""
    return max(SUPPORTED_VERSIONS[kind])


def schema_id(kind: str) -> str:
    """The ``$id`` of a kind's schema, ``urn:agentproof:schema:<kind>-v<version>``.

    A URN is an absolute URI, as draft 2020-12 recommends for a root schema, and implies
    no web host and no distribution name.
    """
    return f"urn:agentproof:schema:{kind}-v{schema_version(kind)}"


def file_name(kind: str) -> str:
    """The file name of a kind's schema under ``schemas/``, ``<kind>-v<version>.schema.json``."""
    return f"{kind}-v{schema_version(kind)}.schema.json"


def schema_for(kind: str) -> dict[str, JsonValue]:
    """The JSON Schema of ``kind`` as a dict: ``model_json_schema()`` plus ``$schema`` and ``$id``.

    Pure. Raises ``KeyError`` for a kind that is not in ``KINDS``.
    """
    schema: dict[str, JsonValue] = {"$schema": SCHEMA_URI, "$id": schema_id(kind)}
    schema.update(KINDS[kind].model_json_schema())
    return schema


def render(kind: str) -> str:
    """The schema of ``kind`` in Canonical form, exactly the text of the committed file."""
    return canonical.dumps(schema_for(kind))
