# Custom full-stack versus low-code delivery

Both editions solve the same assessment problem. Neither is universally better.

| Criterion | Original React / FastAPI / LangGraph | Streamlit / n8n companion |
| --- | --- | --- |
| Interface ownership | Full control over interactions and visual system | Native widgets reduce initial development and frontend ownership |
| Orchestration | Typed code graph with repository tests | Inspectable visual graph with imported/published workflows |
| Business rules | Python pipeline | Independent Python primitives called stage-by-stage by n8n |
| Agent claim | Historical workflow is primarily deterministic LangGraph | Explicitly separate deterministic n8n graph and actual Gemini tool-using AI Agent |
| Retrieval | FastEmbed + PostgreSQL/pgvector | FastEmbed + local fingerprinted NumPy index |
| Persistence | PostgreSQL with application-specific schemas | Isolated SQLite, optional dedicated PostgreSQL via SQLAlchemy |
| Deployment | Separate frontend, API and database | Streamlit plus n8n and a small processing service; hosted components still need proper networking |
| Reliability | Code-level control over job lifecycle | Built-in visual execution records; bounded synchronous webhook has timeout/recovery limitations |
| Maintainability | Familiar code review/testing, more UI implementation | Fast changes for small workflows; complex expressions and large JSON diffs become harder |
| Security | Existing scoped APIs and production controls documented in original repo | Demo password and random workspace capabilities; protected internal endpoints and read-only tools |
| Scaling | Custom service/worker architecture can grow with product needs | Suitable for modest internal tool usage; long-running work needs queues/external runners |
| Expected client need | Branded product, bespoke experience, engineering ownership | Fast operational delivery, visible integrations, limited UI complexity |

For a commercial client I would ask about user count, tenant separation, UI customization, workflow variability, long-running jobs, ownership of changes, deployment access, compliance obligations and support budget. Those constraints determine the architecture. Low-code still needs tested business rules, secrets management, observability and a deployment plan.

The companion's strongest additional evidence is a real Gemini model choosing read-only tools inside n8n. It does not make the deterministic workflow an LLM agent by renaming it. The original application's production acceptance report is historical context, never evidence that this companion has deployed or passed a check.
