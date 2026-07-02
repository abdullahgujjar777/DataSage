# agents/data_concierge.py

import json
import os
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy import text
from dotenv import load_dotenv

from connectors.postgres import get_engine

import re

load_dotenv()

ANALYSIS_PATH = Path("data/schema_analysis.json")


# Token-saving constants

# 10 = 5 Q&A pairs. Beyond this, older turns are dropped entirely.
HISTORY_WINDOW = 10
# Older messages (still within the window) are compressed. 4 = last 2 Q&A pairs full — so follow-up SQL edits always have the original SQL in context.
RECENT_FULL_COUNT = 4


# LLM
def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("FIREWORKS_API_KEY"),
        temperature=0,
        # Fireworks prompt caching: re-bills the system prompt + static docs at
        # ~10% of normal token cost on cache hits. Silently ignored by providers
        # that don't support it, so this is safe to leave on everywhere.
        model_kwargs={"cache_prompt": True},
    )


# Documentation context builder
def _load_docs(path: Path = ANALYSIS_PATH) -> str:
    """Flatten schema_analysis.json into a compact readable string for the prompt."""
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = []
    for t in data["tables"]:
        lines.append(f"Table: {t['table_name']}")
        lines.append(f"  Purpose: {t['purpose']}")
        col_block = "; ".join(
            f"{c['column']} ({c['meaning']})" for c in t["column_meanings"]
        )
        lines.append(f"  Columns: {col_block}")
        if t.get("relationships"):
            lines.append(f"  Relationships: {t['relationships']}")
        for f in t.get("ambiguity_flags", []):
            lines.append(f"  ⚠️  {f['column']}: {f['note']}")
        lines.append("")
    return "\n".join(lines)


# System prompt
SYSTEM_PROMPT = """You are DataSage, an analytical assistant for a business database.
Your job: answer data questions using the documentation below, and write safe, precise SQL
when real figures are needed.

<database_documentation>
{docs}
</database_documentation>

=======================================
STEP 1 — CLASSIFY THE QUESTION
=======================================
Before responding, choose exactly one mode:

  MODE A  EXPLAIN — the question is fully answered by the documentation above
          (schema structure, column meanings, table relationships). No query needed.

  MODE B  QUERY — the question requires real data: counts, totals, rates, trends,
          specific records, or any value that changes over time. Write a SELECT.

  MODE C  OUT OF SCOPE — the question involves tables, columns, or concepts not present
          in the documentation, or is unrelated to this database. Name what is missing.
          If the question ask for unrelated tasks(write eassy for something else, 
          search internet for something, etc) don't do that and apologize.

Ambiguous question: if the question has two plausible SQL interpretations, name both in
"answer", write SQL for the most likely one, and state the assumption you made.

=======================================
STEP 1b — SPLIT MULTI-PART MESSAGES
=======================================
A single user message may contain more than one question. Before doing anything else,
identify every distinct question in the message and treat each one independently.

  - Each question gets its own mode classification (A, B, or C).
  - Each question gets its own entry in the "responses" array in your output.
  - Questions do not share a mode — a message can produce [Mode A, Mode B, Mode C]
    entries simultaneously.
  - The order of entries in "responses" must match the order the questions appeared
    in the message.

A "distinct question" is any request that needs a separate answer or a separate SQL
query. If two sub-questions share a single SQL query naturally (e.g. "what is X and Y
for each order?"), they may be combined into one entry — but only if a single query
genuinely answers both. When in doubt, split.

=======================================
STEP 2 — SQL RULES (MODE B ONLY)
=======================================
Every query MUST:
  - Be a single SELECT statement in valid PostgreSQL.
  - Reference only tables and columns named in the documentation above.
  - Name every column explicitly — never use SELECT *.
  - Apply LIMIT 100 by default. Omit LIMIT only when the query returns a small, fixed
    number of rows by definition (e.g. a single COUNT or SUM with no GROUP BY).
  - Use table aliases and qualified column references (alias.column) whenever two or
    more tables share a column name.

A query MUST NOT contain:
  - Data modification:   INSERT  UPDATE  DELETE  TRUNCATE  MERGE
  - Schema modification: DROP  ALTER  CREATE  RENAME
  - Execution:           EXECUTE  CALL  PERFORM  DO
  - Filesystem access:   COPY  pg_read_file  pg_ls_dir  lo_import
  - Multiple statements (no semicolons separating statements).

=======================================
STEP 3 — WRITE THE RESPONSE
=======================================
For each entry in "responses":

"answer" field:
  - Mode A: directly answer the question in 1–3(or required) plain sentences.
  - Mode B: explain what the result means for the user's actual question. Tell the user
             how to read the result — what each row represents and what the key column
             means. Do not just restate the SQL in English.
  - Mode C: name specifically what is missing or out of scope in 1–2 sentences. Do not
             say "I don't have access to real-time data" — that mischaracterises this
             system.

"sql" field:
  - Mode A or C: JSON null — not the string "null", not an empty string.
  - Mode B: the SELECT statement as a single JSON string value.

"mode" field:
  - Always present. One of the strings "A", "B", or "C".
  - Lets the caller know what kind of response this entry is without parsing "answer".

=======================================
OUTPUT FORMAT — STRICT
=======================================
Return ONLY a valid JSON object. No markdown fences. No text before or after.
Always use the "responses" array — even when there is only one question.

{{
  "responses": [
    {{
      "mode": "A" | "B" | "C",
      "answer": "<string — never null, never empty>",
      "sql": "<SELECT statement, or null>"
    }}
  ]
}}

JSON encoding rules:
  - Escape all double-quotes inside string values as \\"
  - Escape hard newlines inside string values as \\n
  - "answer" must never be null or an empty string.
  - "responses" must never be an empty array — every question gets an entry.

=======================================
GROUND RULES
=======================================
Never invent or assume anything not stated in the documentation:
no table names, no column names, no business logic, no data values.
If something is genuinely unclear or absent from the documentation, respond in Mode C."""


# History compression
def _compress_turn(turn: dict) -> str:
    """Compress a completed Q&A turn into a compact history entry.

    For assistant turns: tries to parse the raw JSON response (if it was stored
    that way), otherwise falls back to truncating the plain-text content.
    For user turns: returned as-is (already short).

    This keeps older context in the window at a fraction of the token cost.
    """
    if turn["role"] == "assistant":
        try:
            data = json.loads(turn["content"])
            lines = []
            for r in data.get("responses", []):
                mode = r.get("mode", "?")
                answer_snippet = r.get("answer", "")[:80]
                sql = r.get("sql")
                if mode == "B" and sql:
                    lines.append(
                        f"[Mode B] Q answered with SQL: {sql[:120]}... | Summary: {answer_snippet}"
                    )
                elif mode == "A":
                    lines.append(f"[Mode A] Explained: {answer_snippet}")
                else:
                    lines.append(f"[Mode C] Out of scope: {answer_snippet}")
            return "\n".join(lines)
        except Exception:
            # History stores plain text (not raw JSON) — just truncate
            return turn["content"][:150]
    return turn["content"]   # user messages stay as-is


def _build_messages(
    system_content: str,
    history: list[dict],
    question: str,
) -> list:
    """Build the LangChain message list with three token optimisations applied:

    1. Prompt caching  — system message is first and static; the provider caches it.
    2. Sliding window  — at most HISTORY_WINDOW messages from history are included;
                         older ones are dropped entirely.
    3. Compression     — messages outside RECENT_FULL_COUNT are compressed to ~150
                         chars; the most recent RECENT_FULL_COUNT messages stay full
                         so follow-up queries (e.g. "now filter by country") retain
                         the SQL that was just generated.
    """
    messages = [SystemMessage(content=system_content)]

    # Apply sliding window first
    windowed = history[-HISTORY_WINDOW:]

    for i, turn in enumerate(windowed):
        # Distance from the END of the list (1 = most recent)
        distance_from_end = len(windowed) - i
        if distance_from_end > RECENT_FULL_COUNT:
            content = _compress_turn(turn)
        else:
            content = turn["content"]

        if turn["role"] == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=question))
    return messages


# SQL safety + execution
def _is_safe_sql(sql: str) -> bool:
    """Defense-in-depth: reject anything that isn't a pure SELECT.
    The read-only DB role already blocks writes at the DB layer —
    this catches it earlier and gives a cleaner error message.
    """
    cleaned = sql.strip().lstrip("(").upper()
    if not cleaned.startswith("SELECT"):
        return False
    forbidden = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "CREATE", "TRUNCATE", "GRANT", "REVOKE", "EXEC",
    ]
    return not any(kw in cleaned for kw in forbidden)


def _enforce_limit(sql: str, cap: int = 100) -> str:
    sql = sql.strip().rstrip(";").strip()
    if re.search(r'\bLIMIT\b', sql, re.IGNORECASE):
        return sql
    is_bare_aggregate = (
        re.search(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', sql, re.IGNORECASE)
        and not re.search(r'\bGROUP\s+BY\b', sql, re.IGNORECASE)
    )
    if is_bare_aggregate:
        return sql
    return f"SELECT * FROM ({sql}) AS _q LIMIT {cap}"


def _execute_sql(sql: str, row_cap: int = 50) -> str:
    """Execute query via read-only engine; return results as a plain text table."""
    sql = _enforce_limit(sql)
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.mappings().all()

        if not rows:
            return "Query returned no rows."

        cols = list(rows[0].keys())
        header = " | ".join(cols)
        divider = "-" * len(header)
        body = [" | ".join(str(row[c]) for c in cols) for row in rows[:row_cap]]

        suffix = f"\n(showing {row_cap} of {len(rows)} rows)" if len(rows) > row_cap else ""
        return "\n".join([header, divider] + body) + suffix

    except Exception as e:
        return f"SQL execution error: {e}"


# Public API
def ask_question(
    question: str,
    history: list[dict],   # [{"role": "user"|"assistant", "content": "..."}]
    docs_path: Path = ANALYSIS_PATH,
) -> list[dict]:
    """Ask a question about the database.

    Args:
        question:  The user's current question (may contain multiple sub-questions).
        history:   Full conversation so far. Caller appends to this after the call.
        docs_path: Path to schema_analysis.json (default: data/schema_analysis.json).

    Returns:
        list of response dicts — one per distinct question found in the message:
        [
            {
                "mode":    "A" | "B" | "C",
                "answer":  str,
                "sql":     str | None,
                "results": str | None,   # populated after SQL execution; not from LLM
            },
            ...
        ]

    Token optimisations applied on every call (all transparent to callers):
        - cache_prompt=True passed to Fireworks → system prompt re-billed at ~10%
          cost on cache hits
        - History windowed to last HISTORY_WINDOW messages
        - Messages older than RECENT_FULL_COUNT compressed to ~150 chars each
    """
    llm = _get_llm()
    docs = _load_docs(docs_path)
    system_content = SYSTEM_PROMPT.format(docs=docs)

    messages = _build_messages(system_content, history, question)

    raw = llm.invoke(messages)

    # gpt-oss-120b quirk: reasoning tokens live in a separate field; use .content only.
    content = raw.content if isinstance(raw.content, str) else raw.content[0]["text"]
    content = content.strip().strip("```json").strip("```").strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return [{"mode": "A", "answer": content, "sql": None, "results": None}]

    responses = parsed.get("responses", [])
    if not responses:
        return [{"mode": "C", "answer": "No response generated.", "sql": None, "results": None}]

    output = []
    for entry in responses:
        sql = entry.get("sql")
        if not sql or (isinstance(sql, str) and sql.strip().lower() == "null"):
            sql = None

        results = None
        if sql:
            if _is_safe_sql(sql):
                results = _execute_sql(sql)
            else:
                results = "⚠️ Unsafe SQL rejected (non-SELECT statement)."

        output.append({
            "mode":    entry.get("mode", "A"),
            "answer":  entry.get("answer", ""),
            "sql":     sql,
            "results": results,
        })

    return output