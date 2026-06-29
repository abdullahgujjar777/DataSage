import json
from datetime import datetime, timezone
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM

from models.analysis_models import TableAnalysis, SchemaAnalysis

from dotenv import load_dotenv
load_dotenv()


SNAPSHOT_PATH = Path("data/schema_snapshot.json")
OUTPUT_PATH = Path("data/schema_analysis.json")

PROMPT_TEMPLATE = """You are a business analyst documenting a database table for a non-technical audience.

Table: {table_name}
Columns (name, type, nullable, FK):
{columns_block}

Sample rows (real data — never invent values):
{samples_block}

Rules:
- Base every claim ONLY on the columns and samples above. Never invent business context.
- Give each column a short, table-specific meaning. No generic definitions.
- "FK=None" means NO confirmed relationship. Even if a column name matches one you've seen
  in another table, do NOT assume a relationship unless FK says so — flag it as ambiguous instead.
- If a column's meaning is genuinely unclear from the data alone, put it in ambiguity_flags
  with the competing interpretations. Do not pick one and present it confidently.
- relationships: only describe links backed by an actual FK in the column list above.
- business_value: 1-2 sentences, what business question this table answers.
"""

def _get_llm() -> LLM:
    return LLM(
        model="fireworks_ai/accounts/fireworks/models/gpt-oss-120b",
        base_url="https://api.fireworks.ai/inference/v1",
    )

def _build_task(agent: Agent, table: dict) -> Task:
    columns_block = "\n".join(
        f"- {c['name']} ({c['type']}, nullable={c['nullable']}, FK={c['foreign_key']})"
        for c in table["columns"]
    )
    samples_block = json.dumps(table["sample_rows"][:5], indent=2, default=str)

    description = PROMPT_TEMPLATE.format(
        table_name=table["table_name"],
        columns_block=columns_block,
        samples_block=samples_block,
    )

    return Task(
        description=description,
        expected_output="A TableAnalysis: purpose, column_meanings, relationships, business_value, ambiguity_flags.",
        agent=agent,
        output_pydantic=TableAnalysis,
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

    tasks = [_build_task(analyst, table) for table in snapshot["tables"]]
    Crew(agents=[analyst], tasks=tasks, process=Process.sequential).kickoff()

    table_analyses = []
    for t in tasks:
        if t.output.pydantic is None:
            raise ValueError(f"Failed to parse structured output:\n{t.output.raw}")
        table_analyses.append(t.output.pydantic)

    return SchemaAnalysis(
        generated_at=datetime.now(timezone.utc).isoformat(),
        tables=table_analyses,
    )

def write_analysis(analysis: SchemaAnalysis, path: Path = OUTPUT_PATH) -> None:
     path.parent.mkdir(parents=True, exist_ok=True)
     path.write_text(analysis.model_dump_json(indent=2), encoding="utf-8")



from markdown_renderer import render_markdown

if __name__ == "__main__":
    analysis = run_analysis()
    write_analysis(analysis)
    Path("data/documentation.md").write_text(render_markdown(analysis), encoding="utf-8")
    print(f"Wrote analysis for {len(analysis.tables)} tables to {OUTPUT_PATH}")

