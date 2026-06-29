import json
from datetime import datetime, timezone
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from dotenv import load_dotenv

from models.analysis_models import SchemaAnalysisDraft, SchemaAnalysis

load_dotenv()

SNAPSHOT_PATH = Path("data/schema_snapshot.json")
OUTPUT_PATH = Path("data/schema_analysis.json")
DOCS_PATH = Path("data/documentation.md")

PROMPT_TEMPLATE = """You are a business analyst documenting an entire database schema for a non-technical audience.

You are given ALL tables in the schema at once, specifically so you can reason across tables —
not just within one. Use that.

{tables_block}

Rules:
- Base every claim ONLY on the columns and samples given. Never invent business context.
- Give each column a short, table-specific meaning. No generic definitions.
- "FK=None" means NO confirmed relationship. If a column name (e.g. "channel" or "status")
  appears in more than one table above with no FK between them, check whether their value
  sets even overlap. If they don't, or there's no FK, explicitly flag it as ambiguous in BOTH
  tables and say so in the note (e.g. "channel here means web/app/in-store; a same-named
  column exists in marketing_campaigns but refers to email/social/paid_search — no confirmed
  relationship between them").
- If a column's meaning is genuinely unclear from the data alone, put it in ambiguity_flags
  with the competing interpretations. Do not pick one and present it confidently.
- relationships: only describe links backed by an actual FK in the column list above.
- business_value: 1-2 sentences per table.
- Return exactly one TableAnalysis per table listed above, same order, same table_name.
"""

def _get_llm() -> LLM:
    return LLM(
        model="fireworks_ai/accounts/fireworks/models/gpt-oss-120b",
        base_url="https://api.fireworks.ai/inference/v1",
        temperature=0.2,   # factual task, not creative — keep it deterministic
        max_tokens=4000,   # cap runaway output cost; raise if you see truncation
    )

def _format_table_block(table: dict) -> str:
    columns_block = "\n".join(
        f"  - {c['name']} ({c['type']}, nullable={c['nullable']}, FK={c['foreign_key']})"
        for c in table["columns"]
    )
    samples_block = json.dumps(table["sample_rows"][:5], indent=2, default=str)
    return f"### Table: {table['table_name']}\nColumns:\n{columns_block}\nSample rows:\n{samples_block}\n"

def _build_task(agent: Agent, tables: list[dict]) -> Task:
    tables_block = "\n\n".join(_format_table_block(t) for t in tables)
    return Task(
        description=PROMPT_TEMPLATE.format(tables_block=tables_block),
        expected_output=f"A SchemaAnalysisDraft with exactly {len(tables)} TableAnalysis entries, one per table above, in order.",
        agent=agent,
        output_pydantic=SchemaAnalysisDraft,
    )

def run_analysis(snapshot_path: Path = SNAPSHOT_PATH) -> SchemaAnalysis:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    analyst = Agent(
        role="Business Analyst",
        goal="Explain database tables in plain business language, flagging ambiguity instead of guessing.",
        backstory="A senior data analyst who values precision over confident-sounding guesses.",
        llm=_get_llm(),
        verbose=True,
    )

    task = _build_task(analyst, snapshot["tables"])
    Crew(agents=[analyst], tasks=[task], process=Process.sequential).kickoff()

    draft = task.output.pydantic
    if draft is None:
        raise ValueError(f"Structured output parse failed. Raw output:\n{task.output.raw}")
    if len(draft.tables) != len(snapshot["tables"]):
        raise ValueError(f"Expected {len(snapshot['tables'])} tables, got {len(draft.tables)} — likely truncation, raise max_tokens.")

    return SchemaAnalysis(generated_at=datetime.now(timezone.utc).isoformat(), tables=draft.tables)

def write_analysis(analysis: SchemaAnalysis, path: Path = OUTPUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(analysis.model_dump_json(indent=2), encoding="utf-8")

if __name__ == "__main__":
    from markdown_renderer import render_markdown
    analysis = run_analysis()
    write_analysis(analysis)
    DOCS_PATH.write_text(render_markdown(analysis), encoding="utf-8")
    print(f"Wrote analysis + docs for {len(analysis.tables)} tables. 1 LLM call this run.")