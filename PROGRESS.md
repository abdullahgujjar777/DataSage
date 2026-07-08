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
  - Budget: $6 credit on Fireworks — keep row samples small, watch token usage
  - `test_llm.py` confirmed working

**Key technical note:** `gpt-oss-120b` returns a separate `reasoning_content` field alongside `content` — downstream agent code must parse only `content`.

**Key files:** `.env`, `test_llm.py`, `requirements.txt`

---

## Module 1 — Demo Database ✅ DONE

**What's done:**
- Schema designed and created: 5 tables — `customers`, `orders`, `products`, `order_items`, `marketing_campaigns`
- Faker-based generator populated: 80 customers, 60 products, 15 marketing_campaigns, 100 orders, ~300 order_items
- Verified internal consistency: order `total_amount` matches sum of its `order_items`; order dates can't precede the customer's signup date
- Committed and pushed to GitHub: `schema.sql`, `generate_demo_data.py`
- Fixed a `.gitignore` encoding bug (UTF-16 silently broke the `.env` exclusion pattern)

**Key decisions:**
- **`channel`** in `orders` (web/mobile_app/marketplace/in_store) vs `marketing_campaigns` (email/social_media/paid_search/affiliate) — no FK, disjoint value sets. Core ambiguity trap.
- **`status`** across 4 tables, each with different value set/lifecycle
- `segment` (customers only) — single-table naming ambiguity
- `marketing_campaigns` intentionally has no FK to any other table

**Key files:**
- `schema.sql`, `generate_demo_data.py`, `.gitignore`

---

## Module 2 — Connector Layer ✅ DONE

**What's done:**
- Pydantic models (`ColumnInfo`, `TableSchema`, `SampleRow`) in `models/schema_models.py`
- Read-only Postgres role `datasage_reader` created via `sql/create_readonly_role.sql`
- Singleton SQLAlchemy engine (`get_engine()`) in `connectors/postgres.py`
- `get_schema(engine)` — auto-discovers tables/columns/types/PKs, declared FKs only (no heuristic inference)
- `sample_rows(engine, table_name, limit=8)` — real sample rows per table

**Key decisions:**
- Rejected column-name-based FK inference — would falsely link `channel` trap columns before Agent 2 reasons about them

**Key files:**
- `connectors/postgres.py`, `models/schema_models.py`, `sql/create_readonly_role.sql`

---

## Module 3 — Schema Snapshot ✅ DONE

**What's done:**
- `schema_snapshot.py` — plain deterministic Python, no LLM
- Writes full schema + 8 sample rows per table to `data/schema_snapshot.json`

**Key decisions:**
- Schema Scout CrewAI agent dropped — LLM fabricated schema instead of calling the tool; no reasoning needed for schema fetching. Replaced with deterministic Python.
- Project is now 2-agent system (Business Analyst, Data Concierge) + deterministic collection step

**Key files:**
- `schema_snapshot.py`, `data/schema_snapshot.json`

---

## Module 4 — Agent 2: Business Analyst ✅ DONE

**What's done:**
- Pydantic models: `TableAnalysis`, `ColumnMeaning`, `AmbiguityFlag`, `SchemaAnalysisDraft`, `SchemaAnalysis`
- Single Agent, single Task, single LLM call analyzing all tables at once
- `build_cross_table_index()` — deterministic Python precomputation of cross-table column collisions, injected as closed checklist into prompt
- `markdown_renderer.py` — pure Python, zero LLM calls
- `render_docs.py` — regenerates docs from cached JSON, zero LLM calls

**Eval results:**
- `channel` trap: ✅ caught — flagged as different concepts, no false link
- `status` trap: ✅ caught — one consolidated flag per table
- `segment` trap: ✅ caught

**Key files:**
- `models/analysis_models.py`, `agents/business_analyst.py`, `markdown_renderer.py`, `render_docs.py`
- `data/schema_analysis.json`, `data/documentation.md`

---

## Module 5 — Agent 3: Data Concierge ✅ DONE

**What's done:**
- `agents/data_concierge.py` — multi-turn chat, Text-to-SQL, Mode A/B/C classification
- SQL safety: app-layer keyword blocklist + DB-level read-only role
- `_enforce_limit()` strips trailing semicolons before subquery wrapping
- `ask_question()` returns `list[dict]` — handles multi-part questions

**Key files:**
- `agents/data_concierge.py`

---

## Module 6 — Streamlit UI ✅ DONE

**What's done:**
- `app.py` — single-file Streamlit app; sidebar connection form, scan button, docs tab, chat tab
- Mode B results rendered as `st.dataframe`; SQL in collapsible expander
- Welcome screen shown before first scan

**Key files:** `app.py`

---

## Module 7 — Privacy Layer ✅ DONE

**What's done:**
- `pii_masker.py` — ~40 PII column-name patterns, replaces values with `[MASKED]`
- `schema_snapshot.py` updated — `pii_masking: bool` param, logs `pii_columns_masked` per table
- UI toggle (on by default); masked columns shown in sidebar expander

**Key files:** `pii_masker.py`, `schema_snapshot.py` (updated), `app.py`

---

## Module 8 — Scale & Robustness Testing ✅ DONE

**What's done:**
- 3 new tables: `suppliers`, `inventory`, `returns` (8 tables total)
- New cross-table traps: `suppliers.country` vs `customers.country`; `status` now spans 6 tables
- Schema drift detection wired into UI sidebar
- `get_engine()` validates connection on init; `ask_question()` wraps LLM call in try/except

**Key files:**
- `add_tables.sql`, `generate_new_tables.py`, `drift_detector.py`, `app.py`

---

## Module 9 — Context Pack + Accuracy Demo ✅ DONE (9d deferred)

**What's done:**

**9a ✅ — Context Pack alias + download button:**
- `write_analysis()` copies `schema_analysis.json` → `data/context_pack.json` via `shutil.copy2`
- Sidebar download button (`⬇️ Download Context Pack`)

**9b ✅ — `use_context_pack` flag:**
- `ask_question()` accepts `use_context_pack: bool = True`
- `_load_raw_schema()` — column names + types only, no meanings/flags/relationships
- Toggle wired in Chat tab

**9c ✅ — Failure question confirmed:**
- Question: *"Compare channel performance between marketing and sales"*
- Raw schema mode: produces UNION ALL across disjoint channel value sets — valid SQL, analytically meaningless
- Context Pack mode: correctly identifies ambiguity, avoids false join
- This is the core proof point for the thesis

**9d ⏸ Deferred:**
- Side-by-side Context Pack Impact tab not implemented — lower priority than MCP demo

**Key files:**
- `agents/business_analyst.py`, `agents/data_concierge.py`, `app.py`, `data/context_pack.json`

---

## Module 10 — Adaptive Architecture + Real Database ✅ DONE

**What's done:**
- `build_cross_table_index()` bug fixed: skips `UNIVERSAL_COLUMNS`, skips columns in >40% of tables (guard: inactive on ≤10 tables), caps at 8 entries per column
- `sample_rows()` adaptive column selection: ≤50 cols → SELECT *; 50–150 cols → 50-col priority budget; 150+ cols → 20-col/3-row hard budget; strings truncated at 150 chars universally
- T2 query routing: `complexity_score` and `tier` computed at scan time, stored in Context Pack top-level metadata; T2 injects full context only for matched tables + FK neighbors
- `SchemaAnalysis` model updated with `complexity_score: float` and `tier: int` fields
- Real database smoke test: **bird-interact-lite** PostgreSQL container, `crypto` database (10 tables, obfuscated column names: `ordervault`, `userstamp`, `riskandmarginpivot`, etc.) — scan completed cleanly, `complexity_score: 89.0`, `tier: 1` confirmed in context_pack.json

**Key decisions:**
- Used bird-interact-lite (`crypto` DB) instead of Pagila — genuine enterprise-style obfuscated naming, Docker-based
- T2 threshold: complexity_score ≥ 250; crypto DB lands in T1 — T2 infrastructure live, activates on larger schemas without code change
- Port conflict (local PG18 + Docker both on 5432) resolved by stopping local service during test

**Key files:**
- `agents/business_analyst.py`, `agents/data_concierge.py`, `connectors/postgres.py`
- `schema_snapshot.py`, `models/analysis_models.py`

---

## Module 11 — MCP Server ✅ DONE

**What's done:**
- `mcp_server.py` in repo root — FastMCP server (stdio transport) exposing 3 tools:
  - `get_context_pack()` — returns full Context Pack JSON; primary tool for Claude to understand the schema
  - `query_documentation(table_name)` — returns single table entry; token-efficient for targeted lookups
  - `check_drift()` — calls `drift_detector.detect_drift()` with absolute baseline path; pure structural diff, no LLM
- All paths resolved via `Path(__file__).parent.resolve()` — cwd-independent, works when Claude Desktop spawns the process
- `load_dotenv(REPO_ROOT / ".env")` with explicit absolute path at module load time — DB credentials available before any tool triggers `get_engine()`
- `sys.path.insert(0, str(REPO_ROOT))` — guarantees local imports resolve correctly

**Verified working:** Confirmed live via Claude Desktop — `get_context_pack()` returned 10-table crypto DB Context Pack (`complexity_score: 89.0`, `tier: 1`, generated 2026-07-08T11:18:08). All 3 tools registered and callable.

**Install:** `pip install "mcp[cli]>=1.0,<2.0"`

**Claude Desktop config:**
```json
{
  "mcpServers": {
    "datasage": {
      "command": "C:\\path\\to\\DataSage\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\DataSage\\mcp_server.py"]
    }
  }
}
```

Standard config path: `%APPDATA%\Claude\claude_desktop_config.json`
MSIX (Store) path: `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`

**Key files:**
- `mcp_server.py`

---

## Module 12 — Docker + Public Deploy ⬜ NOT STARTED

**Plan:**
- Base image: `python:3.13-slim`
- `docker-compose.yml`: `db` (postgres:18) + `app` service; `app` waits on `db` healthcheck
- Seed `db` from `pg_dump` of current populated data in `/docker-entrypoint-initdb.d/` — don't re-run `generate_demo_data.py` at container start
- Test from a clean clone before trusting it
- Public deploy: Neon or Supabase free tier (demo DB) + Streamlit Community Cloud (app)
- Only `datasage_reader` (read-only) credentials in public secrets
- AMD endpoint swap if MI300X capacity opens before Jul 11: `LLM_BASE_URL` + `LLM_MODEL` in `.env`

---

## Module 13 — Submission Prep ⬜ NOT STARTED

**Plan:**

**README structure:**
1. Problem stat (cite the 90% benchmark → 17% real-world accuracy research)
2. Context Pack definition — what it is, what it contains
3. Accuracy demo GIF (same question, raw vs Context Pack)
4. Mermaid architecture diagram (renders natively on GitHub)
5. Quickstart: `docker-compose up` (3 commands max)
6. MCP setup section
7. Known limitations (SQL blocklist, regex-only PII)
8. MIT license

**Demo video (2–3 min):**
Hook (accuracy stat) → channel trap explained → Context Pack Impact (wrong SQL vs right SQL) → MCP in Claude Desktop (tools appearing, channel question answered from flags) → drift detection → close on portability.

**Done when:** repo, README, video, and lablab submission all live before July 11, 2026.

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