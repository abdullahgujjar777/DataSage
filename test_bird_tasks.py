"""
test_bird_tasks.py
Runs all 17 crypto BIRD-Interact tasks through ask_question() in both modes.
Saves results to data/bird_task_results.json and a readable .md report.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from datasets import load_dataset
from agents.data_concierge import ask_question

ANALYSIS_PATH = Path("data/schema_analysis.json")
OUTPUT_JSON   = Path("data/bird_task_results.json")
OUTPUT_MD     = Path("data/bird_task_results.md")


def run_task(amb_query: str) -> dict:
    """Run one task in both modes, return structured result."""
    result = {}

    for mode_name, use_ctx in [("with_context", True), ("without_context", False)]:
        try:
            responses = ask_question(
                question=amb_query,
                history=[],
                docs_path=ANALYSIS_PATH,
                use_context_pack=use_ctx,
            )
            # Take first response (most tasks are single-question)
            r = responses[0]
            # DDL tasks: LLM writes the query in answer (Mode C), not sql
            sql = r.get("sql") or r.get("answer", "")
            result[mode_name] = {
                "mode":    r.get("mode"),
                "sql":     sql,
                "results": r.get("results"),
            }
        except Exception as e:
            result[mode_name] = {
                "mode":    "ERROR",
                "sql":     str(e),
                "results": None,
            }

    return result


def render_md(tasks: list, results: list) -> str:
    lines = ["# BIRD-Interact Crypto Task Results\n"]
    lines.append(f"Total tasks: {len(tasks)}\n")

    for i, (task, res) in enumerate(zip(tasks, results)):
        lines.append(f"---\n## Task [{i}]")
        lines.append(f"**AMB:** {task['amb_user_query']}")
        lines.append(f"**Ambiguity types:** {[a['type'] for a in task['user_query_ambiguity']['critical_ambiguity']]}\n")

        for mode_label in ["with_context", "without_context"]:
            r = res[mode_label]
            lines.append(f"### {'✅ With Context' if mode_label == 'with_context' else '❌ Without Context'}")
            lines.append(f"**Mode:** {r['mode']}")
            if r["sql"]:
                lines.append(f"```sql\n{r['sql']}\n```")
            else:
                lines.append("_No SQL generated_")
            lines.append("")

    return "\n".join(lines)


def main():
    print("Loading dataset...")
    ds = load_dataset("birdsql/bird-interact-lite")["dev"]
    crypto_tasks = [t for t in ds if t["selected_database"] == "crypto"]
    print(f"Found {len(crypto_tasks)} crypto tasks\n")

    all_results = []

    for i, task in enumerate(crypto_tasks):
        print(f"[{i+1}/{len(crypto_tasks)}] {task['amb_user_query'][:80]}...")
        res = run_task(task["amb_user_query"])
        all_results.append(res)

        # Show SQL diff inline
        sql_ctx    = res["with_context"].get("sql", "None")
        sql_no_ctx = res["without_context"].get("sql", "None")
        print(f"  WITH CTX:    {str(sql_ctx)[:120]}")
        print(f"  WITHOUT CTX: {str(sql_no_ctx)[:120]}\n")

    # Save JSON
    output = [
        {
            "task_index": i,
            "amb_user_query": t["amb_user_query"],
            "ambiguity_types": [a["type"] for a in t["user_query_ambiguity"]["critical_ambiguity"]],
            "with_context": r["with_context"],
            "without_context": r["without_context"],
        }
        for i, (t, r) in enumerate(zip(crypto_tasks, all_results))
    ]
    OUTPUT_JSON.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"Saved JSON → {OUTPUT_JSON}")

    # Save MD
    OUTPUT_MD.write_text(render_md(crypto_tasks, all_results), encoding="utf-8")
    print(f"Saved MD  → {OUTPUT_MD}")


if __name__ == "__main__":
    main()