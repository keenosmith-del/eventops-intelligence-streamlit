# Observed test report

Observed on 20 October 2026 (Africa/Johannesburg). Tests and evidence belong to this independent companion, not the original application's historical reports.

## Automated regression

**111 passed, 0 failed, 0 skipped**, final run 1.94 seconds. This duration is one observed local run, not a performance guarantee. One warning: installed Starlette deprecates httpx for its test client; tests still pass. Ruff checks pass. Python source compilation passes.

Raw artifacts: [pytest output](evidence/pytest.txt), [JUnit results](evidence/pytest.xml), [lint](evidence/lint.txt).

Coverage includes actual local embeddings/paraphrase search; three-document counts and provenance; normalized queries and contextual follow-ups; compatible/corrupt index loading; global policy scope; no-hit behavior; generation grounding contract and citation membership; provider HTTP/schema/quota failures; persistence/ownership; ICS/JSON/labelled email/HTML parsing; Unicode/email/ID/date normalization; exact duplicates/conflicting fields and retained evidence; inactive/unregistered/missing identities; supplied event discrepancies; verification idempotency; formula-safe exports; source URL/size/timeout/auth/schema/empty inbox behavior; service authentication; atomic request replay; workflow/record status separation; strict agent outputs/tools/actual-observation citations; synthetic-email data guard; uncertain delivery; all seven Streamlit screens and password gates.

Failure-path provider calls are controlled transports, not claims of live outages or provider quota exhaustion. Retrieval tests use the actual downloaded FastEmbed model and genuine passage/query vectors. Unit agent outputs do not establish model functionality; live evidence below does.

## Real RAG provider execution — passed

[Live RAG artifact](evidence/live-rag.json): FastEmbed generated a 19×384 matrix. Gemini `gemini-3.5-flash-lite` answered:

- Check-in question: cites `POL-003`, answer 08:45 South Africa Standard Time. Provider response ID recorded.
- Contextual cancellation follow-up: cites `POL-002`, answer at least 48 hours. Provider response ID recorded.

Only known synthetic assessment knowledge was sent. Two additional browser questions returned actual generated answers with the same supporting policies. No fake generation was substituted for provider responses.

## Real n8n verification — passed

Final verification request: `ba266447-a7ec-419f-96c5-5021e2a50b39`; actual **n8n execution 9**. Both workflow JSON files were imported and published on installed **n8n 2.42.6**, and production webhooks were called with Header Auth.

| Source   | Actual outcome                   | Parsed count                                  |
| -------- | -------------------------------- | --------------------------------------------- |
| Calendar | Completed public HTTPS ICS read  | 5                                             |
| Email    | Completed Mailtrap API GET reads | 3 explicitly labelled synthetic registrations |
| Web      | Completed public HTTPS JSON read | 5                                             |

Thirteen inputs became twelve records after one duplicate merge: **1 verified, 1 rejected, 10 incomplete**. Ada matched the authoritative active directory/registration; Lindi failed active-status and name checks. Holiday observations lacked event/participant identity and stayed incomplete. A real repeated webhook request returned the original execution ID rather than fetching again.

Evidence: [acceptance result](evidence/live-acceptance.json), [all CSV](evidence/live-all.csv), [verified CSV](evidence/live-verified.csv), [sanitized node-level execution manifest](evidence/n8n-executions.json).

Earlier execution 1 was correctly reported partial because Calendar/Web text-response wrappers expected `body` while this installed node returned `data`. The response-shape bug was diagnosed from actual node outputs and fixed. Executions 4, 6 and 9 demonstrate real three-source success afterward. Earlier invalid input produced a generic workflow HTTP 500; the final explicit rejection branch now returns HTTP 400.

## Genuine Gemini AI Agent — passed

Final **n8n execution 12** used the actual AI Agent node and connected Gemini Chat Model. It selected and called `reference_lookup`, `inspect_findings` and `inspect_evidence`, then produced valid structured intent, explanation, evidence IDs and limitations. Citations were validated against actual tool-returned records. No authoritative record status was changed.

Evidence: [final agent result and actual observable calls](evidence/final-live-agent.json). Earlier actual agent executions 3 and 8 are preserved in [first agent evidence](evidence/live-agent.json), [browser agent result](evidence/browser-agent-result.json), and the node manifest. The manifest includes successful Gemini Chat Model and Code Tool node invocations, rather than merely a workflow JSON assertion. Model hidden chain-of-thought was not exported.

Automatic approval review initially rejected a combined live test because uninspected email could be transmitted to Gemini. The read-only source run was completed separately. All three actual messages were then confirmed to carry the explicit controlled synthetic assessment label and example.com addresses; the bounded synthetic-only agent call was approved and succeeded. A service guard now enforces that demonstration boundary for subsequent analysis.

## Actual browser acceptance — passed

[Browser acceptance record](evidence/browser-acceptance.json) contains 11 observed/asserted checks. Through the actual Streamlit UI:

1. Asked the check-in question; inspected generated answer/citation.
2. Asked a contextual cancellation follow-up; observed `POL-002` answer.
3. Triggered the real workflow; actual **n8n execution 6** completed.
4. Opened persisted results: 8 records (limit 3 per source), 1 verified, 1 rejected, 6 incomplete, 1 duplicate merged.
5. Selected Ada; inspected duplicate inputs/provenance.
6. Selected Lindi; inspected the rejected record.
7. Exercised both CSV download actions; export generation independently matched 8 persisted rows / 1 verified row.
8. Reopened the same request from Execution History.
9. Confirmed saved Gemini explanation/tool evidence restored (actual agent execution 8).
10. Saved a human review note.
11. Asserted persisted note and unchanged deterministic rejection.

Screenshot: [actual Gemini result](evidence/browser-agent.png). Native Streamlit tests additionally render all seven pages; the in-app browser's compact viewport was visually inspected. No exhaustive cross-device/mobile browser matrix or automatic downloaded-file filesystem verification is claimed.

## Live webhook security — passed

[Observed HTTP results](evidence/live-webhook-security.json): missing header **403**; wrong token **403**; invalid input **400**. No external source or model call was needed for these rejected requests. Service endpoint owner/auth/idempotency checks are additionally covered by regression tests.

## Explicitly unverified / incomplete

| Check                                                           | Status                          | Reason                                                                                            |
| --------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------- |
| Public Streamlit URL and complete hosted journey                | Pending                         | Publication/independent hosting approval required                                                 |
| Hosted n8n HTTPS webhook                                        | Pending                         | Only isolated local n8n deployed                                                                  |
| Managed PostgreSQL persistence                                  | Not executed                    | Dedicated connection support implemented; no separate account/database provisioned                |
| Full Linux Docker application build                             | Not executed                    | Additional deployment option prepared; host Python + Docker n8n topology tested                   |
| Real provider timeout / rate-limit outages                      | Not forced                      | Controlled transport tests cover behavior without harming providers                               |
| Commercial authentication, tenant isolation, queued recovery    | Outside delivered demonstration | Workspace capabilities/password and synchronous execution have documented limits                  |
| Broad claim-level hallucination evaluation / general extraction | Limited                         | Citations and conservative schemas checked; unrestricted language/attachments/OCR not implemented |

No public deployment, commercial production readiness, external assessment approval, or 100% rubric score is claimed.
