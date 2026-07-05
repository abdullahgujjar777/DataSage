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






from sqlalchemy import text
from models.schema_models import SampleRow

def sample_rows(engine, table_name: str, limit: int = 8) -> list[SampleRow]:
    query = text(f'SELECT * FROM "{table_name}" LIMIT :limit')

    with engine.connect() as conn:
        result = conn.execute(query, {"limit": limit})
        rows = result.mappings().all()

    return [SampleRow(table_name=table_name, row=dict(row)) for row in rows]