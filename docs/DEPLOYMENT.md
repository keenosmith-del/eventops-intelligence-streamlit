# Deployment

## Observed status

Validated locally on macOS/Python 3.12 with Streamlit 1.66.0, FastEmbed 0.7.4 and n8n 2.42.6. Streamlit runs at `http://127.0.0.1:8501`; isolated n8n runs at `http://localhost:5679`; the protected processor listens on port 8766. These are local URLs, not a public deployment.

No GitHub push, Render update, public exposure, paid service, or managed database provisioning has occurred. The original EventOps deployment is untouched.

## Repeatable local environment

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python scripts/configure_local.py
# Set only this application's Gemini and sandbox Mailtrap settings in .env.
.venv/bin/python scripts/index_knowledge.py
```

Follow the import/publish procedure in [n8n operation](../n8n/README.md), then `./scripts/start_local.sh`. Stop the script to stop Streamlit and its processor; stop the isolated workflow engine with:

```bash
docker compose --env-file .env -f n8n/compose.yaml stop
```

The separate n8n volume preserves workflows, encrypted credentials and local execution history. Back up `.env` and this volume securely; changing the encryption key can make saved credentials unreadable. Do not use `down -v` unless you intend to remove this companion's local n8n data.

The ignored `.env` contains independent webhook/service/encryption tokens. The helper can copy only Gemini/Mailtrap settings from an expressly approved file; it excludes all original database/deployment settings. After credential import, delete `n8n/.local/credentials.json`.

## Full Docker topology

The root `compose.yaml` and `Dockerfile` offer app, processor and n8n on a private compose network with separate storage volumes. This is an additional deployment option; the Linux image build/full-compose runtime was not executed during acceptance. The host Python + isolated n8n topology is the one actually tested.

```bash
docker compose --env-file .env up --build -d
```

Ports for this alternative: Streamlit 8502, n8n 5680. Import/publish using `docker compose exec -T n8n ...` instead of the development compose path. The app's explicit `EVENTOPS_LOCAL_COMPOSE=true` permits only the named `n8n` private host over HTTP. Never set this flag for an internet-facing arbitrary HTTP destination.

## Streamlit Community Cloud

Official requirements checked 20 October 2026:

- [Deployment flow](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy): choose a repository, branch and entrypoint; select a supported Python version.
- [Dependencies](https://docs.streamlit.io/deploy/concepts/dependencies): provide requirements at the appropriate project location.
- [Secrets management](https://docs.streamlit.io/deploy/concepts/secrets): configure secrets outside the repository.

Concrete publishing sequence, requiring the owner's repository/hosting approval:

1. Review and publish this independent project to a new repository. Do not push the original repository or expose `.env`, `storage`, `.streamlit/secrets.toml` or the ignored n8n credential file.
2. Provision a separate durable PostgreSQL database. Use only its `postgresql+psycopg://...` URL, TLS and a dedicated restricted account. Never reuse the v.01 database. The application creates its own `companion_objects` table; commercial migrations/backups are a separate operational task.
3. Host the processor service and n8n independently on private networking. n8n needs `EVENTOPS_PROCESSOR_URL` pointing to that processor. Keep header-authenticated processor endpoints private. Protect the n8n editor with its owner account and expose only necessary production webhooks through HTTPS.
4. Import the workflows and create credentials with the same referenced names/IDs or rebind them in the editor. Set an independent n8n encryption key. Publish both workflows; perform authenticated and unauthenticated checks.
5. In Community Cloud choose `app.py`, Python 3.12, and this repository's `requirements.txt`. `requirements.lock.txt` records the actually tested environment; use those versions for deployment reproducibility if desired by replacing requirements with the reviewed lock contents.
6. Add secrets as top-level values: `PUBLIC_DEMO="true"`, `APP_PASSWORD`, independent service/webhook tokens, dedicated `EVENTOPS_DATABASE_URL`, Gemini configuration and hosted HTTPS `N8N_WEBHOOK_URL` / `N8N_AGENT_URL`. Mailtrap credentials belong to the processor, not the browser. Never configure a hosted app to call localhost.
7. Ensure the FastEmbed cache path is writable, e.g. `FASTEMBED_CACHE_PATH="/tmp/eventops-models"`. The index is rebuildable; cloud model download failure is shown honestly.
8. Run the complete browser journey, confirm all actual source outcomes and a Gemini tool-using agent execution, then record the observed URL and deployment revision.

The current model/index strategy avoids a separate vector database. Hosted RAM/cold-start behavior must be measured on the target platform; local tests do not establish Community Cloud resource headroom. Histories on an ephemeral cloud filesystem are not durable.

## Public operation boundaries

Set the application password, use HTTPS, restrict shared access to synthetic data, establish connector data permissions, set retention and budgets, and monitor failures. The demo's random workspace key is a bearer capability, not commercial account/tenant identity. For real personal data, replace this model with proper authentication and tenant authorization before deployment.

Unfinished runs are left visibly running/uncertain and never falsely marked completed. Investigate in n8n, then reconcile the request ID. There is no automatic worker restart/recovery mechanism in this version.
