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


## Module 3 — Agent 1: Schema Scout ⬜ NOT STARTED
## Module 4 — Agent 2: Business Analyst ⬜ NOT STARTED
## Module 5 — Agent 3: Data Concierge ⬜ NOT STARTED
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
