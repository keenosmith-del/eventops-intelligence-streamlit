# Deployment preparation, not a deployment

The root Compose topology is locally tested. The hosted override is a prepared option requiring a reviewed modern Docker Compose version (supports `!reset`), domains, approved paid/private host capacity, proper credentials and a separate managed PostgreSQL database with TLS. It has not been started or hosted-verified. The gateway permits only the two production webhook paths on the automation domain; the n8n editor and processor have no public published port. Administer n8n through a protected SSH tunnel/VPN, not the gateway. Preserve its encryption key and volume; prefer external n8n task runners for commercial isolation.

For a single private host plus managed PostgreSQL:

1. Review/approve the provider, domain ownership, region, budget, secret placement and access policy.
2. Provision a new independent database/role; set `HOSTED_COMPANION_DATABASE_URL` with TLS. Never use v.01 infrastructure.
3. Build the pinned image, run additive migrations once, restore a test backup and verify tables/history.
4. Set `APP_DOMAIN`, `AUTOMATION_DOMAIN`, demo password and independent service/webhook/encryption credentials. Configure a separately approved controlled HTTPS source if event-specific public transport is required; local fixture data is not a hosted third-party integration.
5. Generate workflows for the private processor hostname, import credentials over the protected admin channel, publish workflows and remove plaintext import files.
6. Review the combined config with `docker compose -f compose.yaml -f deploy/compose.hosted.yaml config` in the target's secret-safe shell; never publish rendered secrets.
7. Only after explicit deployment approval, start the reviewed configuration and perform HTTPS, source, RAG, agent, CSV, history/review, restart and auth acceptance.

A managed-container alternative can host Streamlit and the processor as separate services from the same image, n8n on a private service, and a dedicated database in one region. This uses more service allocations but avoids running a public VM. A consolidated app/processor container needs a reviewed process supervisor and private secondary listener; do not assume a platform forwards a second private port to a free web service.

Streamlit Community Cloud hosts only the Streamlit app. It still needs independently reachable HTTPS automation and a durable DB; splitting across unrelated free services increases network/cold-start dependencies. The recommended interview/development topology is the already tested local Compose stack. For hosted operation prefer one container provider/private network plus dedicated PostgreSQL, choosing capacity from measured headroom rather than assuming a free entitlement.
