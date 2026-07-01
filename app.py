# app.py
"""
DataSage — Streamlit UI
Covers Module 6: connect, scan, documentation, and chat.
"""

import os
import json
import streamlit as st
from pathlib import Path
from dotenv import dotenv_values

# ── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="DataSage",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ────────────────────────────────────────────────────────────────────
ANALYSIS_PATH = Path("data/schema_analysis.json")
DOCS_PATH     = Path("data/documentation.md")
ENV_PATH      = Path(".env")

# ── Session-state initialisation ─────────────────────────────────────────────
def _init_state():
    defaults = {
        "history":     [],           # [{role, content}] for data_concierge
        "scan_done":   ANALYSIS_PATH.exists(),
        "scan_error":  None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── Load .env defaults for the connection form ───────────────────────────────
_env = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}

def _env_default(key: str, fallback: str = "") -> str:
    return _env.get(key, fallback)


# ── Helpers ──────────────────────────────────────────────────────────────────
def _apply_connection_to_env(host, port, dbname, user, password):
    """Inject form values into os.environ so get_engine() picks them up."""
    os.environ["DB_HOST"]     = host
    os.environ["DB_PORT"]     = port
    os.environ["DB_NAME"]     = dbname
    os.environ["DB_USER"]     = user
    os.environ["DB_PASSWORD"] = password


def _run_scan(host, port, dbname, user, password):
    """Run the full Agent 2 pipeline and write artefacts to disk."""
    _apply_connection_to_env(host, port, dbname, user, password)

    # Re-import here so the updated env vars are visible when the modules load
    # (important if the connector's singleton was never created yet this session).
    from connectors.postgres import get_engine          # noqa: F401 — forces engine init
    from agents.business_analyst import run_analysis, write_analysis
    from markdown_renderer import render_markdown

    analysis = run_analysis()
    write_analysis(analysis)
    DOCS_PATH.write_text(render_markdown(analysis), encoding="utf-8")


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔍 DataSage")
    st.caption("AI-powered database documentation & chat")

    st.divider()
    st.subheader("Database Connection")

    db_host = st.text_input("Host",     value=_env_default("DB_HOST", "localhost"))
    db_port = st.text_input("Port",     value=_env_default("DB_PORT", "5432"))
    db_name = st.text_input("Database", value=_env_default("DB_NAME", "datasage"))
    db_user = st.text_input("User",     value=_env_default("DB_USER", "datasage_reader"))
    db_pass = st.text_input("Password", value=_env_default("DB_PASSWORD", ""),
                             type="password")

    st.divider()

    pii_masking = st.toggle(
        "PII Masking",
        value=True,
        help="Mask email / phone / SSN-like values before sending samples to the AI. "
             "Full implementation in Module 7 — toggle is wired and ready.",
    )
    if pii_masking:
        st.caption("🛡️ PII masking **on** — sample values flagged as sensitive will be hidden.")
    else:
        st.caption("⚠️ PII masking **off** — all sample values sent to the AI as-is.")

    st.divider()

    scan_btn = st.button("⚡ Scan Database", type="primary", use_container_width=True)

    if scan_btn:
        st.session_state.scan_error = None
        with st.spinner("Analysing schema — this takes 30–60 s…"):
            try:
                _run_scan(db_host, db_port, db_name, db_user, db_pass)
                st.session_state.scan_done  = True
                st.session_state.history    = []   # fresh chat on re-scan
            except Exception as exc:
                st.session_state.scan_error = str(exc)

        if st.session_state.scan_error:
            st.error(f"Scan failed: {st.session_state.scan_error}")
        else:
            st.success("Scan complete!")

    # Show last-scan timestamp if docs exist
    if ANALYSIS_PATH.exists():
        try:
            meta = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
            ts   = meta.get("generated_at", "")[:19].replace("T", " ")
            st.caption(f"Last scan: {ts} UTC")
        except Exception:
            pass


# ── Main area ────────────────────────────────────────────────────────────────
if not st.session_state.scan_done:
    st.markdown("## Welcome to DataSage")
    st.info(
        "Fill in your database connection on the left and click **⚡ Scan Database** "
        "to generate documentation and unlock the chat assistant."
    )
    st.markdown(
        """
        **What happens during a scan:**
        1. DataSage reads your schema — table names, column types, foreign keys
        2. It samples a handful of rows per table (never a full scan)
        3. An AI analyst turns that into plain-English documentation
        4. You get searchable docs + a chat assistant that knows your data
        """
    )
    st.stop()

# ── Tabs (only shown after first scan) ───────────────────────────────────────
tab_docs, tab_chat = st.tabs(["📄 Documentation", "💬 Ask Questions"])

# ── Documentation tab ─────────────────────────────────────────────────────────
with tab_docs:
    if DOCS_PATH.exists():
        st.markdown(DOCS_PATH.read_text(encoding="utf-8"), unsafe_allow_html=False)
    else:
        st.warning("Documentation file not found. Try running a scan.")

# ── Chat tab ──────────────────────────────────────────────────────────────────
with tab_chat:
    st.markdown("Ask anything about your database — schema, column meanings, or real data queries.")

    # Replay conversation history
    for turn in st.session_state.history:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    # Chat input
    prompt = st.chat_input("E.g. 'Which table tracks revenue?' or 'How many active customers are there?'")

    if prompt:
        # Show the user's message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Call the Data Concierge
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    from agents.data_concierge import ask_question
                    responses = ask_question(
                        question=prompt,
                        history=st.session_state.history,
                        docs_path=ANALYSIS_PATH,
                    )
                except Exception as exc:
                    responses = [{
                        "mode":    "C",
                        "answer":  f"Something went wrong: {exc}",
                        "sql":     None,
                        "results": None,
                    }]

            # Render each response entry
            answer_parts = []
            for i, resp in enumerate(responses):
                answer = resp.get("answer", "")
                mode   = resp.get("mode", "A")
                sql    = resp.get("sql")
                results = resp.get("results")

                # Mode badge (subtle)
                _badge = {"A": "📖 Explanation", "B": "📊 Data Query", "C": "❓ Out of Scope"}
                if len(responses) > 1:
                    st.caption(_badge.get(mode, ""))

                st.markdown(answer)
                answer_parts.append(answer)

                if sql:
                    with st.expander("View SQL", expanded=False):
                        st.code(sql, language="sql")

                if results:
                    with st.expander("Query Results", expanded=True):
                        # Try to render as a table if it looks tabular
                        lines = results.strip().splitlines()
                        if len(lines) >= 3 and " | " in lines[0]:
                            try:
                                import pandas as pd
                                cols = [c.strip() for c in lines[0].split(" | ")]
                                rows = [
                                    [c.strip() for c in line.split(" | ")]
                                    for line in lines[2:]   # skip header + divider
                                    if line.strip() and "showing" not in line
                                ]
                                df = pd.DataFrame(rows, columns=cols)
                                st.dataframe(df, use_container_width=True)
                                # Show truncation note if present
                                if any("showing" in l for l in lines):
                                    note = next(l for l in lines if "showing" in l)
                                    st.caption(note.strip())
                            except Exception:
                                st.text(results)
                        else:
                            st.text(results)

                if i < len(responses) - 1:
                    st.divider()

        # Append to history (assistant content = all answer text joined)
        st.session_state.history.append({"role": "user",      "content": prompt})
        st.session_state.history.append({"role": "assistant", "content": "\n\n".join(answer_parts)})