# Deployment preparation

The authoritative current guide is [Iteration 003 deployment runbook](iterations/003/DEPLOYMENT_RUNBOOK.md), supported by [hosting options](iterations/003/HOSTING_OPTIONS.md), [architecture](iterations/003/DEPLOYMENT_ARCHITECTURE.md), [configuration inventory](iterations/003/SECRETS_AND_CONFIGURATION.md), [database/backups](iterations/003/DATABASE_AND_BACKUPS.md), [smoke/operations](iterations/003/SMOKE_TESTS.md) and [rollback](iterations/003/ROLLBACK.md).

The owner requires an ongoing **R0/$0** solution. The conditional primary option is Oracle Always Free ARM + an independent Neon Free project + a free provider-issued Personal Funnel hostname. Free capacity/account eligibility, live TLS and public hosted acceptance remain pending. No paid plan, account, cloud resource, registry push, public deployment or DNS change was performed. Gemini remains disabled because the owner has not confirmed the existing key's billing status.

`deploy/compose.hosted.yaml` is now standalone; do **not** combine it with the development root Compose file. The optional Funnel and local rehearsal overlays have separate purposes. Older Iteration002 deployment documents are historical preparation, superseded by Iteration003.

Development remains on root `compose.yaml` with its existing preserved volumes. Production preparation and the release rehearsal use separate project names/volumes. A local build or successful CI is not public hosting evidence. See [release readiness](iterations/003/RELEASE_READINESS.md) for passed, pending and blocked conditions.
