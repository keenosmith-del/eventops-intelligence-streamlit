# Interview talking points

1. Same business problem, different delivery constraints: a native Python internal tool plus visible low-code orchestration, independently implemented from the submitted full-stack product.
2. Retrieval has measurable behavior: 30 curated cases, 25 ranked-source cases, explicit ambiguity/no-answer cases and separate factual/citation evaluation. Explain the limits of small-corpus perfect scores.
3. Realistic sources are classified honestly: synthetic event information is fetched through an independent HTTP service, Mailtrap is actually read, and unrelated holidays remain unrelated.
4. Real n8n failures were exercised: one bad source does not erase healthy results. A completed execution does not mean every record verified. An uncertain job is never silently marked complete.
5. The Gemini analyst is a real model choosing three bounded read-only tools. It cannot change identity decisions. Evidence-linked structured explanations, snapshot validation and investigation reuse make the distinction concrete.
6. Additive migrations and compare-and-swap make concurrency/business audit behavior defensible without introducing a large framework or destructively replacing local data.
7. The full Linux stack was built and exercised with PostgreSQL, health checks, internal networking and non-root Python processes. The deployment recommendation follows observed resource behavior, not a Dockerfile-only claim.
8. Ordinary CI requires no Gemini/Mailtrap keys. Local checks are evidence; hosted CI and public deployment remain separate states until actually observed.

Suggested 6-minute flow: policy answer/follow-up (1 minute); event scenario and actual n8n execution/checkpoints (1.5 minutes); verified/duplicate/conflicting/incomplete records and review (1.5 minutes); grounded Gemini tool calls (1 minute); evaluation, failure isolation and deployment boundaries (1 minute).
