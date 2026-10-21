# Secrets and configuration inventory

Use `deploy/production.env.example` → ignored `deploy/production.env`, mode0600. `prepare_environment.py` refuses to overwrite it, refuses tracked secret paths and copies provider inputs only when an approved companion file is explicitly named. Rehearsal uses a different ignored file and independent credentials. Never copy any original v.01 environment, database URL or n8n encryption key.

| Input / setting | Actual consumer | Classification / purpose |
| --- | --- | --- |
| `APP_SITE` | Caddy or release preflight in Funnel mode | Public HTTPS origin; no password/query/path. Initially use provider-issued ts.net URL. |
| `RELEASE_TAG`, `RELEASE_REVISION` | Compose image label/runtime logs/workflow generator/manifest | Public release identity; clean commit for eventual production. Rehearsal records an explicit worktree hash. |
| `EVENTOPS_DATABASE_URL` | App, processor, DB tools | Secret; new dedicated PostgreSQL17 database/role, `sslmode=verify-full&sslrootcert=system`. Never original database. |
| `APP_PASSWORD` | App only | Secret shared controlled-reviewer gate; at least32 characters, independent from service tokens. |
| `N8N_WEBHOOK_TOKEN` | App + encrypted n8n header credential | Secret authorization to trigger either approved workflow. Never browser-visible. |
| `EVENTOPS_SERVICE_TOKEN` | Processor + encrypted n8n header credential | Secret authorization for primitives; app does not need it. |
| `N8N_ENCRYPTION_KEY` | n8n only; private recovery backup | Secret key protecting saved credential objects. Preserve it with the matching n8n state. Never regenerate during upgrades. |
| `N8N_RUNNERS_AUTH_TOKEN` | n8n broker and isolated runner | Independent secret; runner gets no other business credentials. |
| `GEMINI_ENABLED` | App/processor | Defaultfalse; true alone is insufficient for production execution. |
| `GEMINI_FREE_TIER_CONFIRMED` | App/processor/release validator | Defaultfalse; owner attestation of a free-tier/billing-disabled project, not an automated billing guarantee. Owner currently said unknown: leavefalse. |
| `GEMINI_API_KEY` | App + encrypted n8n Gemini credential | Secret; never processor environment, browser, JSON workflow or log. |
| `GEMINI_MODEL` | App provider / validator | Flash-class model; current n8n Chat Model workflow explicitly uses gemini-3.5-flash-lite. Changing models also requires regenerated/reviewed workflow compatibility. |
| `GEMINI_DAILY_LIMIT` | App | Global request ceiling; default8, reviewed max20. No paid provider fallback. |
| `AGENT_DAILY_LIMIT` | Processor | Global reserved investigations/day; default3, reviewed max5. One investigation can use several model turns, bounded by agent iterations. |
| `RUNS_PER_HOUR`, `RUNS_PER_WORKSPACE_HOUR` | Processor | Default30 global/6 workspace, persisted atomic slot claims. Replays return saved state before quota consumption. |
| `MAILTRAP_API_TOKEN`, `MAILTRAP_ACCOUNT_ID`, `MAILTRAP_INBOX_ID` | Processor only | Secret token and private sandbox routing; actual read-only requests, no sending. Owner verifies Free subscription/limits. |
| `EXECUTIONS_DATA_MAX_AGE` | n8n | Default168h retained execution data; encrypted credential/workflow state persists. This does not delete companion histories/reviews. Approve retention before release. |

Production constants are consumed too: `PRODUCTION_MODE=true`, `PUBLIC_DEMO=true`, `KNOWLEDGE_ADMIN_ENABLED=false`, `PRIVATE_N8N_ORIGIN=http://n8n:5678`, exact internal webhook URLs, `PRIVATE_SOURCE_ORIGIN=http://scenario:8090`, `ASSESSMENT_SOURCE_BASE_URL`, FastEmbed cache path, Streamlit CORS/XSRF settings, n8n `WEBHOOK_URL`, runner mode/token/broker settings, secure cookies, diagnostics/community-package restrictions and logging limits. `PUBLIC_SCHEME` controls the proxy's forwarded scheme; rehearsal sets HTTP, Funnel/direct production uses HTTPS.

Rehearsal-only: `BOOTSTRAP_PASSWORD`, `COMPANION_DB_PASSWORD`, `RELEASE_REHEARSAL=true` and loopback ports. They are excluded from the production definition. The rehearsal TLS exception is not accepted as hosted TLS evidence. `N8N_METADATA_URL`/`N8N_API_KEY` remain optional existing code settings and are not provisioned; if enabled later they require separate read-only authorization. No decorative cloud variables or unused credentials were added.

The Funnel host identity/Personal account is configured through the owner's Tailscale daemon, outside application containers; no tailnet key is embedded here. A provider URL, new Neon credentials, independent secrets and approved reviewer access are genuine remaining owner inputs. Existing `kailor.co.za` DNS is untouched.

Rotate an exposed provider key through its owner console, then deliberately update the matching private file/encrypted credential and re-run auth acceptance. Do not rotate the n8n encryption key as though it were a disposable service token: preserve/re-encrypt existing credentials using a reviewed recovery procedure. A lost encryption key cannot be reconstructed from a workflow export.
