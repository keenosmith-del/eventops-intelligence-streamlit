# Hosting decision — strict R0 / $0, checked 21 October 2026

The owner requires ongoing free tiers, no promotional-credit dependency, no paid upgrade/overage, no existing-project reuse and no deployment this iteration. The earlier paid-host suggestion is superseded. No account entitlement, free capacity or zero bill has been verified by logging into a cloud account.

## Recommendation

**Primary conditional option:** one **Oracle Cloud Always Free ARM VM**, the prepared private Compose stack, a **new Neon Free project**, and **Tailscale Personal Funnel** for a provider-issued `*.ts.net` HTTPS address. n8n keeps SQLite, workflows, encrypted credentials and execution history on the VM's persistent volume; it is not replaced or simulated. App histories/reviews live in the separate Neon project. No paid disk, load balancer, registry, DNS subscription or external monitoring service is needed. Use the free-only account state; never upgrade to PAYG to obtain capacity.

**Fallback:** the same containers on separately owned, always-on hardware with Neon Free and the same free ingress. This preserves all application components but depends on owner-managed power/network/availability and is **not an independently cloud-hosted deployment**. If independent cloud hosting is mandatory and Always Free capacity cannot be obtained, there is no verified complete $0 fallback among the managed alternatives below. Stop and report that blocker rather than paying or removing n8n.

`eventops-streamlit.kailor.co.za` is a future alternative for direct Caddy HTTPS using the already-owned domain. It requires explicit DNS approval. No DNS was changed. The provider-issued Funnel URL requires neither buying a domain nor modifying the existing domain.

## Verified options

| Option | Compute / persistence / networking | Verdict for this application |
| --- | --- | --- |
| Oracle Always Free + Neon Free | Current Oracle documentation specifies 1,500 A1 OCPU-hours and 9,000 GB-hours monthly, equivalent to 2 OCPUs/12GB for free-only tenancies; 200GB combined block/boot storage. Private Docker networks remain on one host. | Candidate within $0 quotas, subject to home-region capacity, account acceptance, resource labels and idle reclamation. Start with roughly 2 OCPU/6GB and ordinary boot storage within the free allocation; measure before sizing. |
| Managed Render services + Neon | Managed HTTPS/secret controls are convenient. Free services sleep after 15 idle minutes, share 750 monthly hours, cannot attach durable disks or receive private-network requests. Free Render Postgres expires after 30 days. | Reject for a complete persistent $0 stack. n8n needs durable state, its observed warm memory leaves little headroom on tiny instances, and multiple sleeping services create latency and shared-quota risk. Paid disk/private services are outside budget. |
| Streamlit Community Cloud + separate backend | Streamlit interface and `*.streamlit.app` URL are free. It does not host the processor, n8n or durable local files. The backend still needs a real compute/storage home and HTTPS reachability. | Suitable for UI only, but does not solve the full-stack free-host problem; adds cross-provider auth, cold starts and network dependencies. Keeping the whole interface on the free VM is simpler. |
| Hugging Face Docker Spaces | Official overview lists CPU Basic resources, but currently says creating Docker/Gradio compute Spaces requires a paid plan. Disk is ephemeral, and outbound ports are restricted. | Reject as a guaranteed new free-account solution. A FREE CPU price in a table is not proof that a free account may create the required Docker Space. |
| Owned hardware + free Funnel + Neon | Same real software, durable owned disk and an ongoing-free provider HTTPS hostname; host must remain on. | Closest fully functional free fallback, with an explicit loss of independent cloud availability. No software is replaced by mocks. |

Official references: [Oracle Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), [Free Tier account behavior](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm), [Render free services](https://render.com/docs/free), [Render private networking](https://render.com/docs/private-network), [Render disks](https://render.com/docs/disks), [Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud), [Hugging Face Spaces](https://huggingface.co/docs/hub/en/spaces-overview).

## Cost and quota ledger

| Component | Intended recurring price | Conditions / failure behavior |
| --- | --- | --- |
| A1 host, boot/data storage, basic networking | $0 within verified Always Free allocation | Verify actual console labels and IP/network entitlement before creation; no trial-only shape, paid image, PAYG upgrade, excess volumes or paid support. Capacity is not reserved. Oracle may reclaim idle instances; no artificial load/keepalive scheme is proposed. |
| Neon Free, completely separate project | $0 | Currently 100 CU-hours/project/month, 1GB/project, account storage aggregate limit, 5GB public transfer/project; sleeps after 5 inactive minutes. Compute/transfer exhaustion suspends compute; storage-growing operations fail at the limit. No automatic paid fallback. |
| Tailscale Personal / Funnel hostname / TLS | $0 for eligible personal use | Personal is listed as free indefinitely; Funnel is available on all plans, remains beta and has non-configurable bandwidth limits. Account eligibility and real route/TLS acceptance remain pending. |
| Gemini Flash-Lite | $0 only on confirmed billing-disabled free-tier project | Official `gemini-3.5-flash-lite` pricing includes free input/output tiers. Account billing state is unknown; owner instructed **keep disabled**. No new Gemini call was made for Iteration 003. Quota exhaustion must return unavailable, not select a paid fallback. |
| Mailtrap sandbox reads | Existing approved sandbox | Actual read-only acceptance ran; no messages sent. A free sandbox offering exists, but current account/subscription/quota entitlement is not verified. Retain the free plan and confirm API-read limits before deployment. |
| GitHub public source / standard hosted CI | $0 | This is a public repository; use standard Ubuntu runners, small retained artifacts and no image registry push or paid runner. |
| Logs/backups | Local bounded files and owner-controlled free storage | JSON log rotation is configured. Encrypt and copy backups off-host to approved existing storage/free allocation; no paid backup account is assumed or created. |

Sources: [Neon pricing](https://neon.com/pricing), [Neon limits and limit behavior](https://neon.com/docs/introduction/plans), [Tailscale Personal pricing](https://tailscale.com/pricing), [Funnel availability/limits](https://tailscale.com/docs/features/tailscale-funnel), [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing), [Mailtrap pricing](https://mailtrap.io/pricing/), [GitHub runner pricing](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

The intended sum is **$0**, without credits or paid upgrades, **conditional on obtaining and retaining those exact free entitlements**. It is not an account-level billing guarantee. The specific unresolved hosting blocker is an available ongoing-free persistent backend host; the specific unresolved AI blocker is the key's free-tier/billing status. No current evidence establishes cloud uptime, bandwidth or future pricing guarantees.

## Reliability and operating responsibility

Oracle can reclaim an idle instance based on its published seven-day utilization criteria, and free capacity can be unavailable. Neon cold starts add latency and its free plan has no uptime SLA. Funnel's beta/bandwidth limits add another availability dependency. FastEmbed needs a first-download network request; its persistent cache avoids routine redownload, but a lost host/cache requires warming again. A laptop-backed fallback stops when the laptop sleeps. None is described as production-grade reliability.

The VM owner maintains OS/Docker updates, SSH/firewalls, disk usage, encrypted backup retention, restore tests, free-plan monitoring and incident recovery. TLS can be provided by Funnel initially; direct Caddy renewal is the alternative after DNS approval. Do not run regular SQL health queries or external keepalives to defeat scale-to-zero: those consume Neon quota and do not establish reliability.
