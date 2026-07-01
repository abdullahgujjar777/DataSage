# DataSage — Progress Log

> Source of truth for project status. Update after every module is marked done.
> If switching Claude accounts/projects: paste this file + the Project Instructions into the new project's knowledge.

---

## Module 0 — Environment & Foundations ✅ DONE

**What's done:**
- Python 3.13.1, Git, PostgreSQL 18 installed and verified on Windows
- Virtual environment created with: `sqlalchemy`, `psycopg2-binary`, `crewai`, `langchain-openai`, `python-dotenv`, `streamlit`, `pandas`, `faker`
- GitHub repo live: `abdullahgujjar777/DataSage` (public), `.gitignore` excludes `.env`
- LLM backend decision: **Azure OpenAI dropped** — no obtainable OpenAI quota on Azure for Students. Switched to **Fireworks AI (Serverless)**, which is also AMD's hackathon-sanctioned compute stack.
  - Model: `accounts/fireworks/models/gpt-oss-120b`
  - Endpoint: `https://api.fireworks.ai/inference/v1` (OpenAI-compatible)
  - Credentials in `.env`: `FIREWORKS_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`
  - Budget: $6 credit on Fireworks — keep row samples small, watch token usage once Agent 2/3 testing ramps up
  - `test_llm.py` confirmed working

**Key technical note:** `gpt-oss-120b` returns a separate `reasoning_content` field alongside `content` — downstream agent code must parse only `content`.

**Key files:** `.env`, `test_llm.py`, `requirements.txt` (or equivalent)

---

## Module 1 — Demo Database ✅ DONE

**What's done:**
- Schema designed and created: 5 tables — `customers`, `orders`, `products`, `order_items`, `marketing_campaigns`
- Faker-based generator populated: 80 customers, 60 products, 15 marketing_campaigns, 100 orders, ~300 order_items
- Verified internal consistency: order `total_amount` matches sum of its `order_items`; order dates can't precede the customer's signup date; order `status` correlates with order age (no "pending" order from 11 months ago); campaign `end_date` only populated for "completed" campaigns
- Committed and pushed to GitHub: `schema.sql`, `generate_demo_data.py`
- Fixed a `.gitignore` encoding bug (file was saved as UTF-16, which silently broke the `.env` exclusion pattern) — confirmed `.env` is now actually ignored via `git check-ignore -v .env`

**Key decisions / deviations from plan:**
- Built two deliberate ambiguity traps into the schema, beyond just vague column names — these are the actual eval target for Module 4 (Business Analyst):
  - **`channel`** exists in both `orders` (`web`/`mobile_app`/`marketplace`/`in_store`) and `marketing_campaigns` (`email`/`social_media`/`paid_search`/`affiliate`) — no FK between the two tables, and the value sets don't overlap. Tests whether the agent falsely infers a relationship between same-named columns vs. correctly flags it as unconfirmed.
  - **`status`** exists in 4 tables (`customers`, `products`, `orders`, `marketing_campaigns`), each with a different value set/lifecycle. Tests whether the agent gives table-specific explanations instead of one generic "status tracks record state" answer for all four.
  - `segment` (customers only) is a simpler, single-table naming ambiguity — not a cross-table trap.
- `marketing_campaigns` intentionally has no FK to any other table (see `channel` trap above).
- Data-consistency bugs found and fixed during build (none of these affect the traps above): campaign `end_date` no longer set for active/paused campaigns; `order_date` can't predate `customers.signup_date`; `orders.status` now derives from order age instead of being picked independently of date.
- Known simplification, not a bug: `order_items.unit_price` uses the product's *current* price, not a historical price-at-order-time. Out of scope for the hackathon.

**Key files:**
- `schema.sql` — CREATE TABLE statements for all 5 tables
- `generate_demo_data.py` — Faker population script (run after `schema.sql`; drops and recreates tables each run)
- `.gitignore` — `venv/`, `.env`, `__pycache__/`, `*.pyc`

---

## Module 2 — Connector Layer ✅ DONE

**What's done:**
- Pydantic models (`ColumnInfo`, `TableSchema`, `SampleRow`) in `models/schema_models.py`
- Read-only Postgres role `datasage_reader` created via `sql/create_readonly_role.sql`; verified read succeeds, write fails (`DELETE` → permission denied)
- Singleton SQLAlchemy engine (`get_engine()`) in `connectors/postgres.py` — pooled, cached at module level (`global _engine`), credentials from `.env`
- `get_schema(engine)` — auto-discovers tables/columns/types/PKs, declared FKs only (no heuristic/name-based FK inference, by design — preserves Module 1's `channel`/`status` ambiguity traps)
- `sample_rows(engine, table_name, limit=8)` — real sample rows per table, returns `list[SampleRow]`
- `test_connector.py` — standalone integration test across all 5 tables; confirmed real FKs detected correctly, both `channel` traps correctly show `FK: None`

**Key decisions / deviations from plan:**
- Rejected warehouse-agnostic abstraction (BaseConnector/Factory/ConnectionConfig) from a parallel planning chat — kept function-based design; abstracting before a second warehouse exists means guessing at the interface
- Rejected tracing/fixtures infra for this module — premature with two functions; revisit if Module 3/4 chaining makes failures hard to localize
- Rejected column-name-based FK inference heuristic — would falsely link `channel` trap columns before Agent 2 reasons about them, defeating the Module 1 eval
- Engine made a true module-level singleton (not just "created once") — needed since CrewAI tools (Module 3) will call `get_engine()` repeatedly per run

**Key files:**
- `connectors/postgres.py` — `get_engine()`, `get_schema()`, `sample_rows()`
- `models/schema_models.py` — `ColumnInfo`, `TableSchema`, `SampleRow`
- `sql/create_readonly_role.sql` — read-only role setup (record only, already applied)
- `test_connector.py` — standalone test script

---

## On the horizon (deferred, not urgent)
- **PII masking enhancement (Module 7):** plan is column-name pattern matching only; real DLP/Macie/Purium-style tools also do content-based regex matching on sample values to catch PII in non-obvious columns (`notes`, `bio`, etc.) — log as known limitation + extension path in README, not required for submission
- **Documentation depth control (Module 4/6):** ask user once, pre-scan, if they're familiar with the data → feeds Agent 2's prompt as a mode switch (thorough vs concise) → later exposed as a Module 6 UI toggle. Cheap: it's a prompt-template branch, not new infra.


## Module 3 — Schema Snapshot ✅ DONE
*(originally planned as a CrewAI agent — see "Key decisions" below for why that changed)*

**What's done:**
- `schema_snapshot.py` — plain Python, no LLM. Calls Module 2's connector functions and
  writes the full schema + 8 sample rows per table to `data/schema_snapshot.json`
- Verified: all 5 tables present, FKs intact, `channel`/`status` ambiguity traps preserved

**Key decisions / deviations from plan:**
- Originally built as a CrewAI agent ("Schema Scout") calling a tool. Dropped it after
  testing showed the LLM (Fireworks gpt-oss-120b) wouldn't reliably call the tool —
  it repeatedly fabricated a plausible-but-fake generic e-commerce schema instead of
  executing the function (matches CrewAI issue #3154). A guardrail with live DB
  validation could force correct output via retries, but cost 3-4x the LLM calls for
  a task with zero actual reasoning in it.
- Verdict: there is nothing to reason about in fetching a schema. An agent adds
  unreliability and token cost with no benefit. Replaced with deterministic Python.
- Project is now a 2-agent system (Business Analyst, Data Concierge) plus a
  deterministic data-collection step — not 3 agents. Reflect this in README/submission framing.

**Key files:**
- `schema_snapshot.py` — `collect_schema_and_samples()`, `write_snapshot()`
- `data/schema_snapshot.json` — generated output, Module 4's input
- `test_schema_snapshot.py` — standalone test




## Module 4 — Agent 2: Business Analyst ✅ DONE

**What's done:**
- Pydantic models: `TableAnalysis`, `ColumnMeaning`, `AmbiguityFlag`, `SchemaAnalysisDraft`
  (LLM output, no metadata), `SchemaAnalysis` (saved output, adds `generated_at`) in
  `models/analysis_models.py`
- `agents/business_analyst.py` — single Agent, single Task, single LLM call analyzing all
  5 tables at once — ~5x cheaper than per-table calls, gives the model cross-table visibility
- `build_cross_table_index()` — deterministic Python precomputation: finds every column name
  shared across 2+ tables with no FK, with sampled values per table and overlap, grouped by
  column name (not pairwise) so each table gets ONE consolidated flag per colliding column
  instead of one per other table sharing the name
- `markdown_renderer.py` — pure Python, `render_markdown(analysis)`, zero LLM calls
- `render_docs.py` — regenerates `documentation.md` from cached `data/schema_analysis.json`,
  zero LLM calls, so markdown formatting iteration never touches the API budget
- Verified end-to-end across 3 prompt iterations (see below); final run confirmed clean

**Key decisions / deviations from plan:**
- Switched from 5 separate per-table LLM calls to 1 combined call — cheaper, and the only
  way to give the model visibility into both `channel` columns at once
- Split `SchemaAnalysisDraft` (LLM-facing, no `generated_at`) from `SchemaAnalysis`
  (disk-facing) — LLM never asked to invent a timestamp it can't know
- Cross-table collision detection moved from "ask the model to notice it" to deterministic
  Python checklist injected into the prompt — turns an open-ended task into a closed one,
  scales better as table count grows (Module 8 relevance)
- Index grouped by column name (not pairwise per table-pair) after pairwise version caused
  `status` (4 tables) to generate 3 redundant flags per table instead of 1, and made the
  model falsely flag "active" (a generic shared word) as a possible undeclared relationship
  between unrelated tables (customers/products/marketing_campaigns) — fixed by surfacing all
  colliding tables together and adding explicit guidance to treat small/generic overlaps as
  coincidental, not relational
- `render_docs.py` added as a free, no-LLM rendering path separate from `run_analysis()`

**Eval results (channel/status/segment traps from Module 1) — final run:**
- `channel` trap: ✅ caught — correctly flagged as different concepts, no false link
- `status` trap: ✅ caught — one consolidated flag per table, correctly dismisses "active"
  overlap as coincidental rather than a relationship signal
- `segment` trap: ✅ caught — flags the undefined criteria behind segment labels

**Known operational note:** hit a transient Windows DNS resolution failure
(`getaddrinfo failed`) mid-run once — confirmed as a local network blip (unrelated host
`telemetry.crewai.com` also failed to resolve in the same run), not a Fireworks outage or
code bug. No code changes made for it; real retry/error handling is already scoped for
Module 8.

**Key files:**
- `models/analysis_models.py` — `TableAnalysis`, `ColumnMeaning`, `AmbiguityFlag`,
  `SchemaAnalysisDraft`, `SchemaAnalysis`
- `agents/business_analyst.py` — `run_analysis()`, `write_analysis()`,
  `build_cross_table_index()`
- `markdown_renderer.py` — `render_markdown()`
- `render_docs.py` — `load_analysis()`, no-LLM doc regeneration
- `data/schema_analysis.json` — generated output, Module 5's input
- `data/documentation.md` — final rendered doc




## Module 5 — Agent 3: Data Concierge ✅ DONE

**What's done:**


`agents/data_concierge.py` — complete implementation:

`_load_docs()` — flattens schema_analysis.json into a compact natural-language string for the prompt (cheaper tokens than raw JSON)
`_get_llm()` — LangChain ChatOpenAI pointing at Fireworks endpoint (no CrewAI — single agent, single call, no orchestration needed)
`_is_safe_sql()` — app-level SQL safety guard, rejects any non-SELECT before hitting the DB; defense-in-depth on top of the read-only DB role
`_enforce_limit()` — strips trailing semicolons before subquery wrapping (prevents PostgreSQL syntax errors), skips wrapping for bare aggregates (COUNT/SUM/AVG/MIN/MAX with no GROUP BY) that always return one row
`_execute_sql()` — runs validated SQL via datasage_reader engine, returns results as plain-text table, caps at 50 display rows
`ask_question(question, history, docs_path)` — full public API: builds message list (system + history + question), calls LLM, parses responses array, executes SQL if present, returns list[dict]



`drift_detector.py` — complete:

`detect_drift()` — loads baseline snapshot, re-collects live from DB, diffs tables and columns (additions, removals, type changes, nullability changes)
`format_drift_report()` — human-readable summary
Fully deterministic, no LLM



`test_data_concierge.py` — test suite verified: Mode A (doc-only), Mode B (Text-to-SQL), multi-turn, multi-part questions, Mode C (out of scope) all passing


**Key decisions:**


No CrewAI — Data Concierge is a single LLM call; CrewAI would add overhead with no benefit
LangChain ChatOpenAI used directly — maps to Fireworks endpoint via OpenAI-compatible API
`ask_question` returns `list[dict]` not a single dict — prompt handles multi-part questions and returns a responses array; each entry has `{mode, answer, sql, results}`
Mode A/B/C classification before generation — forces the model to decide question type before answering; reduces hallucinated SQL and vague answers
`results` is added by Python post-execution, not by the LLM — the LLM describes what results will show before they're retrieved; results appear in the next turn's history
Chat history: LLMs are stateless — `history: list[dict]` is rebuilt into the message list on every call; caller owns the list and appends after each turn
Schema drift detection is deterministic Python — no LLM needed; detecting structural changes is pure set-diff, not reasoning
`_enforce_limit()` strips trailing semicolons before wrapping — LLM-generated SQL often includes a trailing semicolon which becomes a syntax error when embedded inside a subquery; stripping it at the enforcement layer fixes this without touching the LLM prompt


**Key files:**


`agents/data_concierge.py` — `ask_question()`, `_load_docs()`, `_is_safe_sql()`, `_enforce_limit()`, `_execute_sql()`
`drift_detector.py` — `detect_drift()`, `format_drift_report()`
`test_data_concierge.py`


## Module 6 — Streamlit UI ⬜ NOT STARTED
## Module 7 — Privacy Layer ⬜ NOT STARTED
## Module 8 — Scale & Robustness Testing ⬜ NOT STARTED
## Module 9 — Submission Prep ⬜ NOT STARTED

---

### Template for new entries
```
## Module X — <Name> ✅ DONE

**What's done:**
- ...

**Key decisions / deviations from plan:**
- ...

**Key files:**
- ...
```
