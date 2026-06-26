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

## Module 1 — Demo Database ⬜ NOT STARTED

**Plan:** Schema for customers, orders, products, order_items, marketing_campaigns (with intentionally ambiguous columns: status, segment, channel) → CREATE TABLEs → Faker population (~50-100 rows/table) → visual verification.

**Done when:** demo DB fully populated, queries return sensible/consistent data.

---

## Module 2 — Connector Layer ⬜ NOT STARTED
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
