# Production readiness: Nimbus Helpdesk (reference answer)

Read this only after writing your own. It is one reasonable review of the EXER041 service, not the only
one. Every gap below points at the Module 9 lesson that closes it.

## 1. Who calls it, and what they may do

| Caller | Today | Needed |
|---|---|---|
| Customer (web chat) | Anyone who can reach port 8000 | An authenticated identity; may ask questions and read their own threads only |
| Staff (internal tool) | Same as customers | Staff identity; may also read the employee handbook through search and save notes |
| The platform | `/healthz`, `/readyz` | Unchanged: health routes stay unauthenticated and reveal nothing |

**Gap:** the client chooses `thread_id`, so anyone who learns or guesses one can continue another person's
conversation. Notes are one file shared by every caller, and search returns staff documents to customers.
**Lecture 042.**

## 2. What can go wrong with money or data

- A tool that changes something (a refund, a note) can run twice: a retry, a resumed checkpoint, or a
  crash between "done" and "saved". Each side effect needs an idempotency key and an audit record.
  **Lecture 043.**
- Conversations, notes and traces hold personal data. There is no retention period and no way to delete
  one person's data. **Lecture 047.**

## 3. Load and failure

| Question | Today | Target |
|---|---|---|
| How many questions at once? | Unbounded threads | A concurrency limit, a bounded queue, 503 + `Retry-After` beyond it |
| One user sends 1,000 questions | All are answered and billed | Per-user rate limit and daily token budget, 429 beyond it |
| A question takes 5 minutes | The caller waits 300 s | A deadline (for example 60 s), then 504 |
| `docker stop` | Ignored for 10 s, then killed mid-answer | `SIGTERM` handler: stop accepting, finish in-flight work, exit |
| A 1 MB request body | Truncated to 20 KB and parsed | 413 |

**SLO proposal:** 99% of questions answered without a 5xx, and 95% within 15 seconds, measured over 28
days. **Lecture 044.**

## 4. Cost

Every question costs about 1,000–3,000 tokens, mostly retrieved passages (EXER037 stretch goal 2).
Repeated questions ("Is shipping free?") could be served from a cache keyed by model, prompt version,
tools, policy and tenant; personal answers must never be cached. The evaluation runs could go through a
batch endpoint where the provider offers one. **Lecture 045.** A cheaper model may answer most questions
as well; measure it before switching. **Lecture 046.**

## 5. Releases

A change to the system prompt, a tool description or the model can break a category that nobody looked
at. Each release runs the capstone evaluation and is compared with an approved baseline per category;
safety may never drop. The baseline names the prompt version it was measured with. **Lecture 048.**

## 6. After launch

Thumbs up/down and implicit signals (the same question asked again within a minute, "talk to a human")
feed a weekly review of sampled traces. Each confirmed failure becomes a new evaluation case.
**Lecture 049.**

## 7. Explicitly out of scope for the first release

Streaming answers, a web framework, multi-region deployment, and a managed vector store. Each is worth
doing; none blocks a safe first release.
