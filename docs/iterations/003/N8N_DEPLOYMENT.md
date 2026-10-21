# Reproducible n8n deployment and safe upgrades

The prepared release uses n8n2.42.6 and matching `n8nio/runners:2.42.6`. These tags have Linux ARM64 and amd64 manifests. Production uses an external runner on a separate internal bridge, non-root/read-only filesystem and a dedicated broker secret. The runner has no provider credentials, application DB access or persistent n8n volume. Its launcher health is distinct from proof that a particular task succeeded.

## Publication

After backing up n8n and preparing the private release file, create `deploy/.local/workflows` before first Compose startup. Import/publish is explicit:

```bash
.venv/bin/python -m deploy.publish --env-file deploy/production.env --publish
```

The publisher generates the two workflows for the exact private processor origin, validates the graph, writes a revision/SHA256 manifest, rebinds the stable header/Gemini credential IDs, imports, publishes stable IDs `EventOpsVerify01` and `EventOpsAgent01`, then restarts only n8n/runner. Credential JSON is sent over stdin into mode0600 container tmpfs and removed by a trap, including failure paths. No plaintext credential JSON is committed or placed in the generated workflow directory.

`--rehearsal` targets only the new local project and ports. The publisher explicitly honors its env file even when the importing Python process has loaded developer `.env`; this prevents unintended key/token replacement. Repeated publication validates only the two workflow files, ignoring its own manifest and any private diagnostic graph.

Workflows carry a deterministic version UUID tied to revision and processor origin. The run's stored `workflow_revision` and execution ID identify what executed; the adjacent manifest hashes identify both actual JSON files. Save that manifest with each release. Current workflows have 31 verification nodes and 11 analyst nodes.

## Acceptance sequence

1. Verify both unauthorized webhook POSTs return401/403 through the private operator connection.
2. Verify the processor rejects missing service credentials and its authenticated readiness query succeeds.
3. Trigger a controlled assessment execution with a new request ID. Confirm Calendar/Email/Web outcomes, record decisions, revision/checkpoints and persistence.
4. Replay the same bound request ID; sources must not run twice. Reconciliation must respect the workspace owner.
5. Check partial-source behavior, exports and review history.
6. Only after owner confirmation of billing-disabled Gemini Free, set both model flags deliberately and run a narrowly bounded analyst/grounded-answer test. Validate actual tool calls and citations. The owner currently requested **keep disabled**; Iteration003 model revalidation is pending.
7. Restart with the same persistent volume and encryption key, then repeat authenticated acceptance. Never automatically replay an unfinished execution after an upgrade.

No public n8n webhook is required in this topology: Streamlit calls n8n over the private bridge. The public gateway rejects all webhook/editor/API routes. Operator access uses SSH/private CLI. Do not attach a public n8n domain, expose5678/5679, disable token auth or weaken secure cookies to make a demo work.

## Credential ownership and failure handling

The app has only its webhook credential and optional RAG Gemini key; the processor has its own service token and Mailtrap token. n8n stores encrypted service/webhook/Gemini credential objects. The processor checks model enablement/free-tier attestation but does not possess the Gemini key. Three analyst tools are read-only snapshot lookups; output validation cannot change deterministic statuses.

A configured external runner isolates ordinary Code-node tasks; it is not a blanket guarantee that every specialized AI integration runs in that sidecar. Keep workflow editing restricted to the owner and do not install unreviewed packages. Environment access from nodes is blocked. A commercial multi-tenant instance would require stronger authorization, execution isolation, monitoring and recovery than this controlled synthetic portfolio.

For runner/broker failure inspect private health/registration logs, fix connectivity/token mismatch, then reconcile before retrying. For Gemini429/quota failure retain unavailable state and wait; no paid fallback. For a failed import preserve the previous manifest/state and inspect private logs. CLI imports do not erase execution history, but deliberate re-import/publication changes the active workflow version.
