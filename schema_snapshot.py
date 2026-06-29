# schema_snapshot.py

import json
from pathlib import Path
from datetime import datetime, timezone
from connectors.postgres import get_engine, get_schema, sample_rows

OUTPUT_PATH = Path("data/schema_snapshot.json")


def collect_schema_and_samples() -> list[dict]:
    """Plain, deterministic schema + sample collection. No LLM involved —
    nothing here needs reasoning, so nothing here gets one."""
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
    return output


def write_snapshot(data: list[dict], path: Path = OUTPUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tables": data,
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8") # default=str handles Decimal/date


if __name__ == "__main__":
    data = collect_schema_and_samples()
    write_snapshot(data)
    print(f"Wrote schema snapshot for {len(data)} tables to {OUTPUT_PATH}")