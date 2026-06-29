# tools/schema_tools.py

import json
from crewai.tools import tool
from connectors.postgres import get_engine, get_schema, sample_rows


def _collect_schema_and_samples() -> str:
    """Plain function — the real logic. Callable directly by the tool below,
    by a guardrail, by a test script, by anything. Not tied to CrewAI at all."""
    engine = get_engine()
    schemas = get_schema(engine)

    output = []
    for table in schemas:
        samples = sample_rows(engine, table.table_name, limit=8)
        output.append({
            "table_name": table.table_name,
            "columns": [col.model_dump() for col in table.columns],
            "sample_rows": [s.row for s in samples],
        })
    return json.dumps(output, default=str)


@tool("Collect Database Schema and Samples")
def collect_schema_and_samples() -> str:
    """
    Connects to the database once and returns the full schema (tables, columns,
    types, PKs, FKs) plus up to 8 sample rows per table, for EVERY table in a
    single call. Never call this more than once.
    """
    return _collect_schema_and_samples()