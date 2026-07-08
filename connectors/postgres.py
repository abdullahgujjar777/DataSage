# connectors/postgres.py

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import os
from dotenv import load_dotenv

from sqlalchemy.exc import OperationalError

load_dotenv()

_engine: Engine | None = None  # module-level cache, starts empty

def get_engine() -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")

    connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    try:
        _engine = create_engine(connection_string, pool_size=5, max_overflow=10, pool_pre_ping=True,connect_args={
                "connect_timeout": 10,             # fail fast if DB is unreachable (seconds)
                "options": (
                    "-c statement_timeout=30000"   # kill any query running >30s (milliseconds)
                    " -c lock_timeout=5000"        # don't hang waiting for locks >5s
                ),
            },
        )
        with _engine.connect():  # validate connection immediately
            pass
    except OperationalError as e:
        _engine = None
        raise ConnectionError(f"Could not connect to database: {e.orig}") from e
    return _engine

def reset_engine() -> None:
    global _engine
    _engine = None

from sqlalchemy import inspect
from models.schema_models import ColumnInfo, TableSchema


def get_schema(engine) -> list[TableSchema]:
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    schemas = []

    for table_name in tables:
        columns_metadata = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = set(pk_constraint.get("constrained_columns", []))

        fk_lookup = {}
        for fk in inspector.get_foreign_keys(table_name):
            referred_table = fk["referred_table"]
            for local_col, remote_col in zip(fk["constrained_columns"], fk["referred_columns"]):
                fk_lookup[local_col] = f"{referred_table}.{remote_col}"

        columns = []
        for col in columns_metadata:
            columns.append(ColumnInfo(
                name=col["name"],
                type=str(col["type"]),
                nullable=col["nullable"],
                is_primary_key=col["name"] in pk_columns,
                foreign_key=fk_lookup.get(col["name"]),
            ))

        schemas.append(TableSchema(table_name=table_name, columns=columns))

    return schemas


def _select_columns_adaptive(columns: list[ColumnInfo], budget: int) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()

    def _add(name: str):
        if name not in seen and len(selected) < budget:
            selected.append(name)
            seen.add(name)

    # Priority 1 — PKs and FK columns
    for c in columns:
        if c.is_primary_key or c.foreign_key is not None:
            _add(c.name)

    # Priority 2 — NOT NULL columns
    for c in columns:
        if not c.nullable:
            _add(c.name)

    # Priority 3 — business-signal patterns
    _PATTERNS = ("_status", "_date", "_amount", "_type", "_name", "_code",
                 "status", "date", "amount", "type", "name", "code")
    for c in columns:
        if any(p in c.name.lower() for p in _PATTERNS):
            _add(c.name)

    # Fill remaining budget in original column order
    for c in columns:
        _add(c.name)

    return selected


def _truncate_strings(row: dict, max_len: int = 150) -> dict:
    return {
        k: (v[:max_len] if isinstance(v, str) and len(v) > max_len else v)
        for k, v in row.items()
    }



from sqlalchemy import text
from models.schema_models import SampleRow

def sample_rows(
    engine,
    table_name: str,
    limit: int = 8,
    columns: list[ColumnInfo] | None = None,
) -> list[SampleRow]:
    n_cols = len(columns) if columns else 0

    if columns is None or n_cols <= 50:
        col_clause = "*"
        row_limit = limit
    elif n_cols <= 150:
        selected = _select_columns_adaptive(columns, budget=50)
        col_clause = ", ".join(f'"{c}"' for c in selected)
        row_limit = limit
    else:
        selected = _select_columns_adaptive(columns, budget=20)
        col_clause = ", ".join(f'"{c}"' for c in selected)
        row_limit = 3

    query = text(f'SELECT {col_clause} FROM "{table_name}" LIMIT :limit')
    with engine.connect() as conn:
        result = conn.execute(query, {"limit": row_limit})
        rows = result.mappings().all()

    return [SampleRow(table_name=table_name, row=_truncate_strings(dict(row))) for row in rows]