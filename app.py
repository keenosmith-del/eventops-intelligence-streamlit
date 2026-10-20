"""EventOps Intelligence — Streamlit Edition."""

import hmac
import json
import os
import secrets

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="EventOps Intelligence", page_icon=":material/hub:", layout="wide"
)
# Streamlit deployment secrets populate server settings before application imports.
try:
    for key, value in st.secrets.items():
        if isinstance(value, (str, int, bool)):
            os.environ.setdefault(
                key, str(value).lower() if isinstance(value, bool) else str(value)
            )
except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
    pass

from eventops.client import explain, trigger
from eventops.config import ROOT, setting
from eventops.knowledge import load_documents
from eventops.pipeline import export_csv, summary
from eventops.rag import SemanticIndex, ask
from eventops.store import Store, now

st.html("""<style>
.block-container {max-width:1280px;padding-top:2.4rem;padding-bottom:3rem;}
h1 {font-weight:550;letter-spacing:-.045em;line-height:1.1;}
h2,h3 {font-weight:500;letter-spacing:-.025em;}
[data-testid="stMetricValue"] {font-weight:450;letter-spacing:-.04em;}
[data-testid="stSidebar"] {border-right:1px solid #deded3;}
[data-testid="stChatMessage"] {border:1px solid #e2e1d7;border-radius:12px;background:#fcfbf7;}
</style>""")

if setting("PUBLIC_DEMO") == "true" and not setting("APP_PASSWORD"):
    st.error(
        "Hosted operation requires an application access password. Configure APP_PASSWORD."
    )
    st.stop()
if setting("APP_PASSWORD") and not st.session_state.get("authenticated"):
    st.title("EventOps Intelligence")
    st.caption("An evidence-led event operations workspace")
    with st.form("sign-in"):
        password = st.text_input("Workspace password", type="password")
        if st.form_submit_button("Open workspace", type="primary"):
            if hmac.compare_digest(password, setting("APP_PASSWORD")):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("The password is incorrect.")
    st.stop()

if "owner" not in st.session_state:
    st.session_state.owner = secrets.token_hex(24)
store = Store()
owner = st.session_state.owner


@st.cache_resource(show_spinner=False)
def semantic_index():
    return SemanticIndex()


def heading(eyebrow, title, subtitle):
    st.caption(eyebrow.upper())
    st.title(title)
    st.write(subtitle)
    st.space("small")


def runs():
    return store.list(owner, "run")


def metrics(records):
    counts = summary(records)
    cols = st.columns(5)
    for col, key, label in zip(
        cols,
        ["total", "verified", "review_required", "rejected", "duplicates_merged"],
        ["Records", "Verified", "Review required", "Rejected", "Duplicates merged"],
    ):
        col.metric(label, counts[key])
    if counts["incomplete"]:
        st.caption(f"{counts['incomplete']} records are incomplete.")


def overview():
    heading(
        "EventOps / Intelligence",
        "Traceable event operations.",
        "An event operations workspace for grounded knowledge, autonomous source processing, and transparent verification.",
    )
    docs = load_documents()
    history = runs()
    cols = st.columns(3)
    cols[0].metric("Knowledge documents", 3)
    cols[1].metric("Authoritative records", len(docs))
    cols[2].metric("Saved executions", len(history))
    st.divider()
    a, b = st.columns(2, gap="large")
    with a:
        st.subheader("01 / Find the authoritative answer")
        st.write(
            "Ask about event schedules, admission rules, or participant records. Inspect semantic matches and the evidence behind each generated response."
        )
        st.page_link(
            assistant_page,
            label="Open Knowledge Assistant",
            icon=":material/arrow_forward:",
        )
    with b:
        st.subheader("02 / Process and verify")
        st.write(
            "Run the visual n8n workflow across Calendar, Email, and Web. Review discrepancies, compare references, and export verified records."
        )
        st.page_link(
            agent_page, label="Open Agent Workspace", icon=":material/arrow_forward:"
        )
    st.space("medium")
    with st.container(border=True):
        st.subheader("Evidence before confidence")
        st.write(
            "Retrieved evidence, AI explanations, tool calls, and deterministic decisions remain distinct throughout the workspace. A model cannot promote an uncertain record to verified."
        )
        st.caption(
            "Sample directory uses synthetic identities. Public holiday sources are observations, not event registrations."
        )
    st.subheader("System readiness")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Component": "Semantic retrieval",
                    "State": (
                        "FastEmbed index ready"
                        if (ROOT / "storage/index.npz").exists()
                        else "Builds on first query"
                    ),
                    "Meaning": "Real local embeddings; no lexical substitute",
                },
                {
                    "Component": "Gemini generation",
                    "State": (
                        "Configured"
                        if setting("GEMINI_ENABLED") == "true"
                        and setting("GEMINI_API_KEY")
                        else "Unavailable"
                    ),
                    "Meaning": "Connectivity confirmed only by an actual response",
                },
                {
                    "Component": "n8n orchestration",
                    "State": (
                        f"Last run: {history[0]['payload']['status']}"
                        if history
                        else "No execution in this workspace"
                    ),
                    "Meaning": "A configured URL is not execution evidence",
                },
                {
                    "Component": "Persistence",
                    "State": (
                        "PostgreSQL"
                        if setting("EVENTOPS_DATABASE_URL").startswith("postgresql")
                        else "Local SQLite"
                    ),
                    "Meaning": "Cloud local files are ephemeral; use a dedicated durable database",
                },
            ]
        ),
        hide_index=True,
        width="stretch",
    )


def render_answer(item):
    response = item["response"]
    st.caption(
        f"{response['status'].replace('_', ' ').upper()} · {response.get('model', 'No model response')}"
    )
    st.write(response["answer"])
    if response.get("citation_ids"):
        st.caption("Cited records: " + " · ".join(response["citation_ids"]))
    with st.expander("Retrieved source evidence"):
        if not item["evidence"]:
            st.info("No matching source evidence.")
        for hit in item["evidence"]:
            st.markdown(
                f"**{hit['id']}** · {hit['kind']} · cosine similarity {hit['similarity']:.3f}"
            )
            st.write(hit["content"])
            st.caption(hit["source"])
    with st.expander("Retrieval inspection"):
        st.json(
            {
                "question": item["plan"]["question"],
                "interpreted_intent": item["plan"]["kind"] or "general knowledge",
                "query_transformation": item["plan"],
                "retrieval": item["retrieval"],
                "matched_records": [
                    {"id": r["id"], "similarity": r["similarity"]}
                    for r in item["evidence"]
                ],
                "generation": response,
            }
        )


def assistant():
    heading(
        "Knowledge / Assistant",
        "Ask with context.",
        "Search the three authoritative documents and inspect the records behind the answer.",
    )
    with st.expander("Answer settings"):
        generate = st.checkbox(
            "Generate a grounded Gemini answer",
            value=setting("GEMINI_ENABLED") == "true",
        )
        depth = st.slider("Retrieval depth", 1, 10, 5)
        st.caption(
            "Generation is bounded by the server daily budget. Citation membership is validated; this is not a proof of factual entailment."
        )
    history = list(reversed(store.list(owner, "question", 20)))
    if not history:
        st.caption("Try a question from the actual documents")
        cols = st.columns(3)
        for col, q in zip(
            cols,
            [
                "What are the check-in rules for EVT-101?",
                "Where is EVT-102 held?",
                "How early must I cancel my registration?",
            ],
        ):
            if col.button(q, width="stretch"):
                st.session_state.example_question = q
    for row in history:
        with st.chat_message("user"):
            st.write(row["payload"]["plan"]["question"])
        with st.chat_message("assistant"):
            render_answer(row["payload"])
    question = st.chat_input(
        "Ask about an event, policy, or participant…", max_chars=1000
    )
    question = question or st.session_state.pop("example_question", None)
    if question:
        previous = history[-1]["payload"]["plan"]["event_id"] if history else None
        with st.spinner("Retrieving source evidence and preparing the answer…"):
            try:
                ask(semantic_index(), store, owner, question, previous, depth, generate)
            except Exception as exc:
                if isinstance(exc, ValueError):
                    st.error(str(exc))
                else:
                    st.error(
                        "Semantic retrieval could not start. Check model availability and local index configuration. No fallback answer was generated."
                    )
                return
        st.rerun()


def agent_workspace():
    heading(
        "Operations / Agent",
        "One trigger. An auditable run.",
        "n8n connects the sources and orchestrates each processing stage. Deterministic rules decide verification outcomes.",
    )
    tab_run, tab_workflow, tab_reasoning = st.tabs(
        ["Run verification", "Visual workflow", "Gemini analyst"]
    )
    with tab_run:
        st.info(
            "Calendar and Web defaults contain real public holidays. They test live connectivity and stay labelled as event observations. Mailtrap reads only the configured synthetic-data sandbox."
        )
        with st.form("execute"):
            event = st.selectbox(
                "Target event",
                [r["id"] for r in load_documents() if r["kind"] == "event"],
            )
            limit = st.slider("Maximum records per source", 1, 5, 3)
            submitted = st.form_submit_button("Run verification", type="primary")
        if submitted:
            with st.spinner("Waiting for the actual n8n execution…"):
                result = trigger(store, owner, event, limit)
            st.session_state.selected_run = result["run_id"]
            st.session_state.last_delivery = result
            st.rerun()
        result = st.session_state.get("last_delivery")
        if result:
            st.subheader("Latest request")
            st.write(f"Status: {result['status']} · Request: {result['run_id']}")
            if result.get("error"):
                st.warning(result["error"])
            if result.get("execution_id"):
                st.caption(f"n8n execution {result['execution_id']}")
                st.page_link(
                    results_page,
                    label="Inspect verification results",
                    icon=":material/fact_check:",
                )
        st.caption(
            "No automatic retry follows an uncertain webhook delivery. Reconcile the request ID in Execution History or n8n before retrying."
        )
    with tab_workflow:
        graph = json.loads((ROOT / "n8n/verification.json").read_text())
        st.graphviz_chart(
            """digraph {rankdir=LR; node [shape=box style=rounded color="#959c88" fontname="Arial"]; Trigger -> Validate -> Calendar -> Email -> Web -> Extract -> Normalize -> Deduplicate -> Verify -> Review -> Persist; Validate -> Replay [label="same request"]; Calendar -> Partial [label="failure"]; Partial -> Extract;}"""
        )
        st.caption(
            "Workflow design. Execution evidence is shown in saved source outcomes and the actual n8n execution record."
        )
        st.dataframe(
            [{"Node": n["name"], "Implementation": n["type"]} for n in graph["nodes"]],
            hide_index=True,
            width="stretch",
        )
        st.download_button(
            "Download importable verification workflow",
            (ROOT / "n8n/verification.json").read_bytes(),
            "eventops-verification.json",
            "application/json",
        )
    with tab_reasoning:
        st.write(
            "The Gemini AI Agent node interprets your question and selects read-only tools to inspect findings, authoritative references, and raw evidence. Its explanation cannot change record statuses."
        )
        history = runs()
        completed = [r for r in history if r["payload"]["status"] != "running"]
        if not completed:
            st.info("Finish a verification execution first.")
        else:
            run_id = st.selectbox(
                "Execution to explain", [r["id"] for r in completed], key="agent_run"
            )
            intent = st.text_area(
                "What should the analyst investigate?",
                "Explain which records need attention and why. Compare discrepancies with authoritative references and raw source evidence.",
                max_chars=1000,
            )
            if st.button("Ask Gemini analyst", type="primary"):
                try:
                    with st.spinner(
                        "Waiting for Gemini and its selected tools in n8n…"
                    ):
                        response = explain(owner, run_id, intent)
                    st.session_state.agent_response = response
                    st.session_state.agent_response_run_id = run_id
                except Exception:
                    st.error(
                        "The agent did not return a validated result. Inspect n8n execution logs and provider configuration; deterministic results remain available."
                    )
            response = (
                st.session_state.get("agent_response")
                if st.session_state.get("agent_response_run_id") == run_id
                else None
            ) or store.get(owner, run_id)["payload"].get("agent", {})
            render_agent(response)
        st.download_button(
            "Download importable Gemini agent workflow",
            (ROOT / "n8n/gemini-agent.json").read_bytes(),
            "eventops-gemini-agent.json",
            "application/json",
        )


def render_agent(agent):
    st.caption("AGENT STATUS · " + agent.get("status", "not_requested").upper())
    if agent.get("result"):
        st.subheader("AI-generated explanation")
        st.write(agent["result"]["summary"])
        st.caption("Evidence IDs: " + ", ".join(agent["result"]["evidence_ids"]))
        with st.expander("Interpreted intent and limitations"):
            st.json(agent["result"])
    if agent.get("tool_calls"):
        with st.expander("Actual agent tool calls", expanded=False):
            for call in agent["tool_calls"]:
                st.write(f"**{call['tool']}**")
                st.json(call)
    if agent.get("execution_id"):
        st.caption(
            f"n8n execution {agent['execution_id']} · {agent.get('model')} · {agent.get('note')}"
        )


def select_run():
    history = runs()
    if not history:
        st.info(
            "No saved verification executions in this workspace. Start in Agent Workspace."
        )
        return None
    ids = [r["id"] for r in history]
    selected = st.session_state.get("selected_run")
    run_id = st.selectbox(
        "Saved execution",
        ids,
        index=ids.index(selected) if selected in ids else 0,
        format_func=lambda rid: (
            f"{next(r['created_at'][:19] for r in history if r['id'] == rid)} UTC · {rid[:8]}"
        ),
    )
    return store.get(owner, run_id)["payload"]


def results():
    heading(
        "Verification / Results",
        "Every outcome has evidence.",
        "Inspect the deterministic checks, review uncertain records, and download the persisted results.",
    )
    run = select_run()
    if not run:
        return
    st.caption(
        f"WORKFLOW {run.get('status', 'unknown').upper()} · Request {run.get('run_id', run['request_id'])} · n8n execution {run.get('execution_id', 'not recorded')}"
    )
    if run["status"] == "running":
        st.warning(
            "This run has not recorded completion. It may still be running or may have been interrupted. Check n8n before attempting another delivery."
        )
    records = run["records"]
    metrics(records)
    st.subheader("Source outcomes")
    if run["outcomes"]:
        st.dataframe(run["outcomes"], hide_index=True, width="stretch")
    choices = st.multiselect(
        "Filter by verification status",
        ["verified", "review_required", "rejected", "incomplete"],
    )
    filtered = [r for r in records if not choices or r["status"] in choices]
    display = [
        {
            k: r.get(k)
            for k in [
                "id",
                "event_id",
                "full_name",
                "email",
                "title",
                "record_type",
                "status",
                "duplicate_count",
                "review_status",
            ]
        }
        for r in filtered
    ]
    st.dataframe(display, hide_index=True, width="stretch")
    a, b = st.columns(2)
    a.download_button(
        "Download all records · CSV",
        export_csv(records),
        "eventops-all.csv",
        "text/csv",
        width="stretch",
    )
    b.download_button(
        "Download verified only · CSV",
        export_csv(records, True),
        "eventops-verified.csv",
        "text/csv",
        width="stretch",
    )
    if filtered:
        rid = st.selectbox(
            "Inspect a record",
            [r["id"] for r in filtered],
            format_func=lambda x: next(
                (r["full_name"] or r["title"] or x) + " · " + r["status"]
                for r in filtered
                if r["id"] == x
            ),
        )
        r = next(r for r in filtered if r["id"] == rid)
        tabs = st.tabs(
            [
                "Verification checks",
                "Raw and normalized",
                "Evidence and references",
                "Duplicates",
                "Review",
            ]
        )
        with tabs[0]:
            st.caption("DETERMINISTIC BUSINESS RULES")
            st.dataframe(
                r["checks"],
                hide_index=True,
                width="stretch",
                key="checks-" + run["run_id"] + rid,
            )
            st.write(
                "Findings: "
                + (", ".join(r["issues"]) or "All applicable checks passed.")
            )
        with tabs[1]:
            st.json(
                {
                    "raw": r["raw"],
                    "normalized": {
                        k: r[k]
                        for k in [
                            "event_id",
                            "participant_id",
                            "full_name",
                            "email",
                            "title",
                            "starts_at",
                            "venue",
                        ]
                    },
                }
            )
        with tabs[2]:
            for evidence in r["evidence"]:
                st.caption(evidence["source"] + " · " + evidence["reference"])
                st.code(evidence["excerpt"], language=None)
            st.json({"authoritative_matches": r["matches"]})
        with tabs[3]:
            st.write(
                f"{r['duplicate_count']} duplicates merged · {r['duplicate_type'].replace('_', ' ')}"
            )
            st.dataframe(
                [
                    {
                        k: item.get(k)
                        for k in [
                            "source",
                            "source_record_id",
                            "full_name",
                            "email",
                            "event_id",
                            "venue",
                            "starts_at",
                        ]
                    }
                    for item in r["inputs"]
                ],
                hide_index=True,
                width="stretch",
            )
            if r["conflicts"]:
                st.json({"conflicting_values": r["conflicts"]})
            if r.get("potentially_related"):
                st.caption(
                    "Potentially related records (not merged): "
                    + ", ".join(r["potentially_related"])
                )
            with st.expander("All retained duplicate inputs"):
                st.json(r["inputs"])
        with tabs[4]:
            with st.form("review"):
                review = st.selectbox(
                    "Human review status",
                    ["unreviewed", "investigating", "resolved_with_note"],
                )
                note = st.text_area("Review note", max_chars=2000)
                if st.form_submit_button("Save review"):
                    if not note.strip():
                        st.error("Add a note explaining the review.")
                    else:
                        r["review_status"] = review
                        store.replace(owner, run["run_id"], run)
                        store.save(
                            owner,
                            "review",
                            {
                                "run_id": run["run_id"],
                                "record_id": rid,
                                "review_status": review,
                                "note": note,
                                "at": now(),
                            },
                        )
                        st.success(
                            "Review saved. The deterministic verification status is unchanged."
                        )
            notes = [
                x["payload"]
                for x in store.list(owner, "review")
                if x["payload"]["record_id"] == rid
                and x["payload"]["run_id"] == run["run_id"]
            ]
            if notes:
                st.dataframe(notes, hide_index=True, width="stretch")
    render_agent(run.get("agent", {}))


def sources():
    heading(
        "Knowledge / Sources",
        "Three documents. Stable provenance.",
        "Structured rows preserve event associations and source identifiers through retrieval and verification.",
    )
    docs = load_documents()
    cols = st.columns(3)
    for col, filename, kind in zip(
        cols,
        ["events.csv", "policies.csv", "directory.json"],
        ["event", "policy", "participant"],
    ):
        with col:
            st.metric(filename, sum(r["kind"] == kind for r in docs))
            st.caption("Validated reference records")
    st.caption(
        "Directory identities are synthetic assessment data. These documents are authoritative for this demonstration only."
    )
    for filename, kind in [
        ("events.csv", "event"),
        ("policies.csv", "policy"),
        ("directory.json", "participant"),
    ]:
        with st.expander(filename, expanded=kind == "event"):
            st.dataframe(
                [r["fields"] for r in docs if r["kind"] == kind],
                hide_index=True,
                width="stretch",
            )
            st.download_button(
                "Download " + filename,
                (ROOT / "data/structured" / filename).read_bytes(),
                filename,
            )
    if st.button("Validate and build semantic index"):
        try:
            with st.spinner("Validating sources and generating local embeddings…"):
                index = semantic_index()
            st.success(
                f"{len(index.records)} records indexed with actual {index.vectors.shape[1]}-dimensional FastEmbed embeddings."
            )
            st.code(index.signature, language=None)
        except Exception:
            st.error(
                "Index could not be built. Check model download access and the source validation logs."
            )


def history():
    heading(
        "Workspace / History",
        "Return to the evidence.",
        "Saved executions and questions belong to your workspace access key.",
    )
    rows = runs()
    st.dataframe(
        [
            {
                "Request ID": r["id"],
                "Created UTC": r["created_at"],
                "Event": r["payload"]["event_id"],
                "Workflow status": r["payload"]["status"],
                "n8n execution": r["payload"].get("execution_id", ""),
                "Records": len(r["payload"]["records"]),
            }
            for r in rows
        ],
        hide_index=True,
        width="stretch",
    )
    if rows:
        selected = st.selectbox("Reopen execution", [r["id"] for r in rows])
        if st.button("Open saved results"):
            st.session_state.selected_run = selected
            st.switch_page(results_page)
    st.subheader("Saved questions")
    questions = store.list(owner, "question")
    st.dataframe(
        [
            {
                "Question": r["payload"]["plan"]["question"],
                "UTC": r["created_at"],
                "Response": r["payload"]["response"]["status"],
            }
            for r in questions
        ],
        hide_index=True,
        width="stretch",
    )
    pending = store.list(owner, "request")
    if pending:
        with st.expander("Uncertain webhook deliveries"):
            st.json([r["payload"] for r in pending])
    with st.expander("Recover or change workspace"):
        st.caption(
            "Your workspace key is a private access capability. Keep it to reopen history after a browser session ends. Never share it publicly."
        )
        st.text_input("Current workspace key", owner, type="password", disabled=True)
        st.download_button(
            "Save workspace access key",
            owner,
            "eventops-workspace-key.txt",
            "text/plain",
        )
        with st.form("restore-workspace"):
            key = st.text_input("Existing workspace key", type="password")
            if st.form_submit_button("Restore workspace"):
                if len(key) == 48 and all(c in "0123456789abcdef" for c in key):
                    st.session_state.clear()
                    st.session_state.owner = key
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Enter the 48-character key saved from this application.")


def methodology():
    heading(
        "Architecture / Methodology",
        "A small system, explicit boundaries.",
        "A companion implementation of the same assessment using Streamlit and visual orchestration.",
    )
    st.graphviz_chart(
        """digraph {rankdir=TB; node [shape=box style=rounded fontname="Arial"]; Streamlit -> FastEmbed [label="semantic retrieval"]; FastEmbed -> Gemini [label="retrieved evidence"]; Streamlit -> n8n [label="protected webhook"]; n8n -> Calendar; n8n -> Mailtrap; n8n -> Web; n8n -> Python [label="focused processing primitives"]; Python -> References [label="authoritative comparison"]; Python -> Persistence; n8n -> Agent [label="optional AI Agent node"]; Agent -> GeminiChat; Agent -> ReadOnlyTools; Streamlit -> Persistence;}"""
    )
    st.write(
        "Structured rows form natural retrieval units: each contains a complete event, policy, or participant identity with its original identifier. FastEmbed generates local semantic vectors. Cosine search ranks eligible records after event and category filtering. Gemini receives only retrieved context, and citations must refer to those records."
    )
    st.write(
        "n8n performs source reads, conditional routing, aggregation, replay handling and stage orchestration. Python implements schema validation, parsing and deterministic comparison. The Gemini AI Agent is an optional analyst with three read-only tools, a five-iteration bound, and a structured output validator. Its explanations are saved separately from verification decisions."
    )
    for title, filename in [
        ("Architecture and data flow", "ARCHITECTURE.md"),
        ("Design decisions", "DESIGN_DECISIONS.md"),
        ("Assessment evidence", "ASSESSMENT_COMPLIANCE.md"),
        ("Observed test results", "TEST_REPORT.md"),
        ("Interview walkthrough", "INTERVIEW_WALKTHROUGH.md"),
    ]:
        path = ROOT / "docs" / filename
        if path.exists():
            with st.expander(title):
                st.markdown(path.read_text())


with st.sidebar:
    st.markdown("### EventOps Intelligence")
    st.caption("STREAMLIT EDITION")
    st.space("small")
overview_page = st.Page(
    overview, title="Overview", icon=":material/home:", default=True
)
assistant_page = st.Page(assistant, title="Knowledge Assistant", icon=":material/chat:")
agent_page = st.Page(agent_workspace, title="Agent Workspace", icon=":material/hub:")
results_page = st.Page(
    results, title="Verification Results", icon=":material/fact_check:"
)
sources_page = st.Page(
    sources, title="Knowledge Sources", icon=":material/library_books:"
)
history_page = st.Page(history, title="Execution History", icon=":material/history:")
methodology_page = st.Page(
    methodology, title="Architecture & Methodology", icon=":material/account_tree:"
)
nav = st.navigation(
    {
        "Workspace": [overview_page, assistant_page, agent_page, results_page],
        "Reference": [sources_page, history_page, methodology_page],
    }
)
with st.sidebar:
    st.space("large")
    st.caption("AI explanations inform.\nAuthoritative rules verify.")
    st.caption(
        "Local SQLite is not durable cloud storage."
        if not setting("EVENTOPS_DATABASE_URL").startswith("postgresql")
        else "Dedicated PostgreSQL persistence configured."
    )
nav.run()
st.space("large")
st.caption("EventOps Intelligence · Streamlit Edition / Evidence-led event operations")
