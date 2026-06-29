# agents/schema_scout.py

import os
import json
from typing import Any, Tuple

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tasks.task_output import TaskOutput

# --- workaround for CrewAI bug #5886: cache_breakpoint gets injected into
# every message regardless of provider, but only the Anthropic adapter
# strips it back out before sending. Fireworks rejects the unknown field.
import crewai.llms.cache as _crewai_cache
_crewai_cache.mark_cache_breakpoint = lambda msg: msg

from tools.schema_tools import collect_schema_and_samples, _collect_schema_and_samples

load_dotenv()

llm = LLM(
    model=f"openai/{os.getenv('LLM_MODEL')}",   # "openai/" prefix matters for litellm routing
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)


def validate_schema_output(result: TaskOutput) -> Tuple[bool, Any]:
    """Checks the agent's output against the real, live database schema —
    not a hardcoded list — so fabricated/hallucinated output gets rejected
    and retried instead of silently passing through."""
    expected_tables = {t["table_name"] for t in json.loads(_collect_schema_and_samples())}

    try:
        data = json.loads(result.raw)
    except (json.JSONDecodeError, TypeError):
        return (False, "Output is not valid JSON. Call the tool and return its exact output.")

    if not isinstance(data, list):
        return (False, "Output must be a JSON array, not wrapped in any other key.")

    found_tables = {t.get("table_name") for t in data}
    if found_tables != expected_tables:
        missing = expected_tables - found_tables
        extra = found_tables - expected_tables
        return (False, f"Table mismatch — missing: {sorted(missing)}, unexpected: {sorted(extra)}. "
                        "Call the 'Collect Database Schema and Samples' tool and return its "
                        "exact output instead of writing the schema yourself.")

    for t in data:
        if "columns" not in t or "sample_rows" not in t:
            return (False, f"Table '{t.get('table_name')}' is missing 'columns' or 'sample_rows'.")

    return (True, result.raw)


schema_scout = Agent(
    role="Database Schema Collector",
    goal="Retrieve the complete, unmodified schema and sample data for every table in one tool call.",
    backstory=(
        "You are a mechanical data-collection agent. You do not interpret, summarize, "
        "or reason about what the data means. You call your one tool exactly once and "
        "pass its output through unchanged."
    ),
    tools=[collect_schema_and_samples],
    llm=llm,
    max_iter=3,              # hard cap — this should never need more than 1-2 iterations
    allow_delegation=False,
    verbose=True,
)

scout_task = Task(
    description=(
        "Call the 'Collect Database Schema and Samples' tool exactly once — it already "
        "covers every table. Do not call any other tool. Return its JSON output exactly "
        "as given: no summarizing, no commentary, no reformatting, and never write the "
        "schema from memory or imagination."
    ),
    expected_output=(
        "A JSON array, one object per table, each with table_name, columns, and "
        "sample_rows — identical to the tool's raw output."
    ),
    agent=schema_scout,
    guardrail=validate_schema_output,
    guardrail_max_retries=3,
)

schema_scout_crew = Crew(
    agents=[schema_scout],
    tasks=[scout_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    result = schema_scout_crew.kickoff()
    print(result)