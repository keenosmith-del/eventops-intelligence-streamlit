# Custom full-stack and low-code delivery

| Concern | Original React/FastAPI/LangGraph | Streamlit/n8n companion |
| --- | --- | --- |
| Product surface | Full interaction/design-system control | Native Python internal-tool delivery |
| Workflow ownership | Typed code graph and developer review | Visible source connections, branches and actual n8n execution data |
| Rules | Python verification | Independent Python stage primitives; same authority boundary |
| Agent reasoning | Do not infer model direction from a deterministic graph | Explicit Gemini AI Agent with actual tool evidence and validated advisory output |
| Retrieval | FastEmbed/pgvector in original architecture | Lightweight fingerprinted vectors, measured curated evaluation |
| Persistence | Existing PostgreSQL-specific application | Additive SQLAlchemy schema/revisions, SQLite and tested separate local PostgreSQL |
| Reliability | Custom lifecycle/worker evolution possible | Checkpoints, atomic replay, conservative reconciliation; no queue recovery claim |
| Changes/maintenance | More custom UI work, precise engineering control | Fast small workflow changes; complex graphs/expressions can become harder |
| Security/scaling | Original controls are independently documented | Read-only tools/private services; commercial identity/tenancy remains future work |
| Hosting | Separate custom frontend/API/database | Tested local containers; hosted private services/durable DB still need approval |

Neither approach is universally superior. Choose based on expected users, customization, workflow complexity, job length, data governance, deployment access, engineering ownership and support budget. Low-code does not remove the need for tested business rules, state transitions, secret management or measured deployment capacity.

The companion source repository is public. Both iterations' application acceptance is local; no public application deployment is implied by GitHub publication. The original project and infrastructure remain out of scope.
