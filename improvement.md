# AI Engineering Course Review and Improvement Plan

## Overall assessment

This is a **strong, unusually complete introductory AI application-engineering course**. It succeeds at taking a learner with limited Python experience from a raw model request to a production-style agent system.

The strongest design decisions are:

- **Raw implementation before frameworks.** Learners build HTTP requests, message loops, and tool handling before LangChain or LangGraph abstracts them.
- **A coherent project domain.** Nimbus Coffee gives the RAG, agent, safety, evaluation, and deployment lessons continuity.
- **Measurement throughout.** Prompt accuracy, retrieval hit rate, RAG evaluation, tool trajectories, memory recall, token use, and cost are treated as engineering concerns rather than afterthoughts.
- **Responsible safety framing.** The course does not claim that delimiters, regexes, or better prompts solve prompt injection.
- **Runnable learning artifacts.** Every exercise has starter code, a solution, checks, success criteria, and two stretch goals.
- **Good progression.** The sequence from APIs through RAG, agents, MCP, evaluation, context engineering, and deployment has few prerequisite jumps.

> **A very good course in building LLM applications, especially RAG and agent systems. It is not yet a complete production AI engineering curriculum, but it is honest about that boundary.**

## Review scope and validation

The review covered the current working tree, including its pre-existing EXER040/041 renumbering and context-engineering additions.

Verified:

- 41 lecture pages and 41 corresponding exercises exist.
- Every exercise has `README.md`, `check.py`, `starter/`, `solution/`, and `stretch/`.
- All 246 Python source files parse successfully.
- No local lecture `href` or `src` targets are broken.
- All 41 quizzes validate:
  - 170 questions;
  - four answer options per question;
  - explanations for every option;
  - balanced correct-answer positions: 42, 44, 43, and 41.
- 127 external URLs were checked. Of those, 126 returned a successful response. The Azure pricing URL returned HTTP 301, a normal redirect rather than a dead link.

`check_all.py` was not run during the read-only review because many checks and imports can create reports, SQLite files, indexes, caches, or other artifacts. Syntax, structure, links, and quiz validation were checked without writing bytecode.

---

## 1. Topic coverage

### Covered particularly well

#### LLM API fundamentals

Modules 0 and 1 establish enough underlying knowledge before introducing frameworks:

- HTTP requests and response bodies;
- authentication and configuration;
- SDK clients;
- tokens and cost;
- sampling parameters;
- messages and roles;
- multimodal content blocks;
- streaming;
- structured output;
- retries and concurrency.

That foundation makes the later framework code less magical. The explanation of temperature in `Lecture/lectures/lec004.html` is appropriately qualified: temperature zero does not guarantee identical output.

#### Tool use and agent control

The progression through EXER016–018 and EXER026–031 is one of the best parts of the curriculum:

1. tool calling by hand;
2. framework-provided tools;
3. a security-sensitive shell tool;
4. graph state and reducers;
5. ReAct-style loops;
6. persistence;
7. human approval;
8. agentic retrieval;
9. multi-agent coordination.

The course repeatedly distinguishes rules that can be requested in a prompt from rules that must be enforced in code. The warning in `Lecture/lectures/lec030.html` not to let a model control an unbounded loop is concise and correct.

#### RAG

The RAG sequence is comprehensive for this course level:

- embeddings and cosine similarity;
- loading different file formats;
- chunking and stable document identifiers;
- persisted vector search and source metadata;
- grounded generation;
- BM25 and hybrid search;
- reciprocal-rank fusion and MMR;
- query rewriting and reranking;
- retrieval and generation evaluation;
- a document-chat interface.

The curriculum correctly teaches that retrieval and generation must be evaluated separately. The worked example in `Lecture/lectures/lec024.html` makes that distinction concrete.

#### Evaluation

Evaluation is not confined to one late lesson. It develops in stages:

- labelled prompt classification in EXER008;
- retrieval hit rate in EXER023;
- RAG faithfulness and correctness in EXER024;
- capstone behavioural cases in EXER037;
- tool-call trajectories in EXER038;
- recall versus token use in EXER039;
- accuracy versus context size in EXER040.

The course also warns about tiny evaluation sets, prompt overfitting, averages hiding severe failures, LLM-judge biases, nondeterministic judge results, and overly strict exact trajectory matching.

#### Safety

The safety coverage is stronger than most introductory courses. In particular:

- shell commands use argument lists with `shell=False`;
- allowed programs and dangerous arguments are checked separately;
- the EXER018 string filter is explicitly described as bypassable;
- production isolation is described as a container or VM without secrets or unrestricted networking;
- prompt injection is treated as unresolved rather than fixed;
- sensitive tools are excluded through least privilege;
- consequential operations receive human approval;
- output checks are presented as detectors for anticipated patterns, not proofs of safety;
- observability guidance warns that traces can contain user data.

The core message in `Lecture/lectures/lec036.html` is correct: reduce the blast radius because some attacks will get through.

#### Context management

EXER039 and EXER040 distinguish:

- trimming;
- summarization;
- retrieval over prior turns;
- structured long-term memory;
- tool-result projection;
- sub-agent context isolation;
- setup cost versus recurring cost;
- main-call token reduction versus total token use;
- context position and irrelevant noise.

The context-engineering exercise correctly counts the sub-agent's tokens rather than presenting only the smaller main-agent prompt as a saving.

### Topics mentioned but not taught deeply

These are not necessarily defects because `Plan.MD` explicitly excludes some of them.

#### Model adaptation

Fine-tuning and distillation are mentioned but not taught. There is no practical coverage of supervised fine-tuning, LoRA or PEFT, preference tuning, dataset contamination, adaptation evaluation, distillation, or quantization.

For an application-engineering course this omission is defensible. For a broadly titled AI Engineering course, it should remain explicitly out of scope or become a separate advanced module.

#### Model serving and inference systems

Ollama is used as a provider, but learners do not study prefill versus decode, continuous batching, KV or prefix caching, throughput versus latency, GPU memory constraints, quantized serving, inference servers, or autoscaling inference workloads.

This is a reasonable boundary for an introductory application course, but it separates the curriculum from a broader model-platform engineering course.

#### Audio and real-time systems

Image input is covered. Audio, speech, and real-time streaming interfaces are not. These are lower priority than the production gaps below.

---

## 2. Technical correctness

### High priority: correct the container shutdown claim

Relevant locations:

- `Lecture/lectures/lec041.html:83`
- `EXER041/solution/Dockerfile:39-40`
- `EXER041/solution/service.py:173-186`

The lecture says that exec-form `CMD` makes the service process 1 and lets it receive the stop signal directly, **“so it can shut down cleanly.”**

Exec form does ensure that Python receives `SIGTERM` directly. However, the service only catches `KeyboardInterrupt`; it does not install a `SIGTERM` handler that calls `server.shutdown()` or `server.server_close()`. The default Unix response to `SIGTERM` is process termination, not an application-managed graceful shutdown.

Recommended correction:

- Say that exec form allows the process to receive termination signals directly.
- Either avoid promising graceful shutdown or add a lesson step that handles `SIGTERM`, stops accepting requests, waits for in-flight work within a deadline, and closes the server.

### Medium priority: qualify the reasoning-before-score claim

In `Lecture/lectures/lec024.html:54-70`, the course says that putting the reasoning field before the score improves judgments.

The structured rationale is pedagogically useful because it exposes why a judge assigned a score. The stronger claim that field order improves judgment needs better qualification or supporting evidence. It may also encourage reliance on generated reasoning instead of a concise, auditable rubric justification.

A safer pattern would be to:

- request a short evidence-based justification;
- require cited claims or rubric criteria;
- treat the justification as diagnostic, not ground truth;
- validate the judge against human-labelled examples;
- report judge disagreement.

Repeated model agreement is not the same as agreement with a human evaluator.

### Medium-low priority: distinguish the implemented metric from RAGAS faithfulness

`Lecture/lectures/lec024.html:47` describes RAGAS faithfulness as the share of answer claims inferable from context. The exercise implements a single ordinal score from 1 to 5 in `EXER024/solution/evaluate.py:43-52`.

That is a valid simplified classroom metric, but it is not the claim-level proportion described in the RAGAS definition.

Recommended clarification:

> The exercise uses a simpler 1–5 judge score inspired by the same idea; it does not reproduce RAGAS's claim-decomposition metric.

### Medium-low priority: narrow the delimiter wording

`Lecture/lectures/lec008.html:37` says delimiters “help against injection.” Lecture 036 later provides the necessary qualification: delimiters improve instruction separation but do not provide a security boundary.

Recommended wording:

> Separates instructions from data; useful prompt structure, but not a prompt-injection defence by itself.

### Low priority: remove a source warning

`EXER020/starter/ingest.py:39` produces a Python `SyntaxWarning` because `\s` appears in a normal docstring. It does not break parsing or execution. A raw docstring or escaped backslash would remove the warning.

### Deployment simplifications are appropriately disclosed

The deployment code in `EXER041/solution/service.py` is intentionally educational rather than production-ready. Its limitations include:

- client-selected `thread_id`;
- no authentication or authorization;
- no per-user namespace binding;
- no rate limiting;
- no durable state;
- a synchronous standard-library HTTP server;
- a 300-second assistant timeout;
- no overload or queue control;
- oversized bodies are truncated rather than answered with HTTP 413;
- no graceful termination handling.

These are not concealed defects. `Lecture/lectures/lec041.html:174-180` explicitly identifies most of the missing production work. The course's **production-style** label is accurate.

---

## 3. Structure and progression

### What works

The curriculum has a strong dependency order:

1. Foundations
2. Direct model interaction
3. LangChain abstractions
4. Tool calling
5. RAG
6. LangGraph agents
7. MCP
8. Safety, observability, and capstone
9. Evaluation, memory, context, and deployment

No major concept appears before its prerequisites.

All 41 lecture pages have the intended ten-section structure. The median lecture is approximately 1,213 extracted words; the shortest is about 732 words and the longest approximately 2,194. This consistency helps navigation and expectations.

Earlier concepts also return in more demanding forms:

- messages become graph state;
- token counts become cost and context budgets;
- prompt classification evaluation becomes RAG and agent evaluation;
- local memory becomes persistent and retrieval-based memory;
- tool execution becomes least privilege and human approval;
- source citations become grounded capstone behaviour.

### Structural improvements

#### Rename or reposition Module 8

“Beyond the Capstone” contains material central to a production-minded AI engineer: agent evaluation, memory strategies, context engineering, and deployment. Calling these “beyond” can imply optional enrichment.

Possible alternatives:

- **Module 8: Operating and Improving AI Systems**
- **Module 8: Evaluation, Context, and Deployment**

#### Move or integrate EXER038 with EXER037

The capstone evaluation checks whether expected tools appeared, while the following exercise introduces richer trajectory checks for order and arguments.

Consider teaching the conceptual core of EXER038 before EXER037 and using trajectory evaluation in the capstone's definition of done. The existing post-capstone scoring work could remain as a stretch goal.

#### Reconsider the time estimate for dense late lessons

Lecture 040 is approximately 2,194 extracted words and combines section budgets, projections, sub-agents, token accounting, position effects, and noise experiments. Seventy-five minutes for both the lecture and practical work may be optimistic for the target learner. Lectures 036 and 041 are also comparatively dense.

Options:

- split context budgeting and tool-result shaping from position and noise;
- keep one part as a required lesson and one as a lab;
- raise the time estimate.

---

## 4. Learning design and assessment

### Strengths

Every exercise contains 5–12 automated checks. The checks generally validate behaviour rather than merely importing a function. Notable strengths include:

- starter code must fail, preventing vacuous checks;
- offline fake models keep most checks reproducible;
- live checks are visibly tagged;
- deployment routes are tested independently from sockets;
- the Dockerfile receives static checks;
- dangerous shell examples are explicitly tested;
- quiz schema and coverage have their own validator.

The two stretch goals per exercise are also meaningful: one extends the current idea and one connects it to another lesson.

The capstone rubric in `EXER037/README.md` asks learners to review correctness, grounding, tool use, safety, observability, and code quality. Its written review questions require learners to discuss failures and remaining risk, not just produce passing code.

### Assessment improvements

#### Add a real course-check CI workflow

The repository has a GitHub Pages deployment workflow in `.github/workflows/pages.yml`, but no workflow runs:

```bash
uv sync --frozen
uv run python check_all.py --offline
```

The README describes the offline command as CI-friendly, but CI does not enforce it. Adding this workflow would continuously validate:

- all reference solutions;
- intentionally incomplete starters;
- quiz coverage and schema;
- compatibility with the lockfile.

Priority: **high**.

#### Add independent transfer tasks

Many checks necessarily confirm implementation shape. That is useful for guided exercises, but passing does not always demonstrate conceptual mastery.

At selected module endings, add a short task where the learner applies the idea to a different domain or altered data shape without starter scaffolding. Good candidates include:

- end of Module 1: a new classifier or extractor;
- end of RAG: a new document collection and evaluation set;
- end of agents: a new tool policy and failure case;
- after deployment: a written production-readiness design.

#### Expand the capstone evaluation set

Current dataset sizes include:

- RAG evaluation: 20 cases;
- guardrail suite: 11 cases;
- capstone: 8 cases;
- trajectory evaluation: 6 cases;
- memory probes: 6 cases;
- context probes: 6 cases.

These are suitable teaching sets, and the course warns against overinterpreting them. However, the capstone's 80% threshold over eight cases is coarse: one case changes the result by 12.5 percentage points.

A stronger capstone would use:

- a visible development set;
- a small held-out set;
- categories such as grounding, refusal, arithmetic, memory, tool use, and safety;
- per-category scores rather than only overall pass rate.

Priority: **medium-high**.

#### Add judge-versus-human calibration

The course discusses LLM-judge bias but does not have learners calculate agreement against human labels.

An extension could include 10–20 pre-labelled answer pairs and ask learners to report:

- exact agreement;
- adjacent-score agreement;
- disagreements by category;
- whether changing the judge model or rubric changes the result.

Priority: **medium**.

---

## 5. Recommended additions

### Priority 1: Production identity and data boundaries

The largest practical gap is authentication and authorization. An advanced lesson should teach learners to:

- validate an authenticated identity;
- derive `user_id` or tenant from the credential, not request JSON;
- bind `thread_id` to that identity;
- namespace memory and notes per user;
- authorize every stateful tool server-side;
- test cross-user access attempts;
- distinguish authentication from authorization.

Suggested project:

> Add bearer-token authentication to the helpdesk, bind conversations and notes to a user namespace, and prove that user A cannot read or continue user B's thread.

This is more important than another agent pattern.

### Priority 2: Operations under load

The reliability lesson covers retries and limited concurrency, and observability covers spans and token cost. Missing production mechanisms include:

- bounded queues and backpressure;
- request deadlines and cancellation;
- per-user and global rate limits;
- overload responses;
- latency distributions and p50/p95/p99;
- service-level indicators and objectives;
- load testing;
- graceful shutdown with in-flight requests.

Suggested project:

> Put a concurrency limit and bounded queue in front of the capstone, run a local load test, and report throughput, p50/p95 latency, timeout rate, and rejected requests.

This would bridge EXER011, EXER035, and EXER041.

### Priority 3: CI/CD and release evaluation

The course says evaluation should gate releases but does not implement that process. Add a workflow that:

1. installs from the lockfile;
2. runs offline exercise checks;
3. runs deterministic capstone cases;
4. compares evaluation metrics with an approved baseline;
5. fails on category regressions;
6. leaves live-model evaluation as a manually triggered or credentialed job;
7. preserves evaluation reports as workflow artifacts.

This turns “evaluation as definition of done” into an operational practice.

### Priority 4: Privacy and data lifecycle

PII redaction and trace retention are mentioned, but privacy is not developed into a system-design topic. A lesson should cover:

- data minimization before model calls;
- provider retention and training settings;
- trace and conversation retention;
- deletion workflows;
- user consent and disclosure;
- regional processing or data residency;
- sensitive-field encryption;
- deletion across primary stores, indexes, caches, and backups;
- what must never enter prompts or traces.

Suggested exercise:

> Implement deletion of one user's conversation, memory, notes, and vector-store entries, then verify that retrieval and logs no longer expose the data.

### Priority 5: Prompt and response caching

Coverage could include:

- exact response caches;
- semantic caches and their correctness hazards;
- prompt-prefix caching;
- cache keys that include model, prompt version, tools, and safety policy;
- invalidation and tenant isolation;
- avoiding caches for personalized or rapidly changing responses;
- measuring hit rate, latency, cost, and stale-answer rate.

This fits naturally after context engineering.

### Priority 6: Model selection and routing

The course supports multiple providers but mostly treats the configured model as fixed. A practical lesson could compare models using the existing evaluation framework across:

- quality;
- latency;
- input and output cost;
- structured-output reliability;
- tool-selection reliability;
- context limits;
- safety behaviour.

Learners could then build a deterministic router for cheap classification, expensive ambiguous cases, provider fallback, and escalation when quality signals are poor.

### Priority 7: Optional model adaptation track

If the intended scope expands beyond application engineering, add a separate optional track covering:

1. when prompting, RAG, tools, or fine-tuning addresses the problem;
2. dataset construction and train/validation/test separation;
3. supervised fine-tuning and LoRA;
4. overfitting and catastrophic forgetting;
5. evaluation against the untuned model;
6. distillation and quantization;
7. serving and monitoring the adapted model.

This should remain optional because it requires a different compute and conceptual budget.

---

## 6. Prioritized action list

### Fix now

1. Correct the graceful-shutdown claim in `Lecture/lectures/lec041.html`, or implement `SIGTERM` handling in the deployment exercise.
2. Qualify the “reasoning before score improves judgments” claim in `Lecture/lectures/lec024.html`.
3. Clarify that the 1–5 faithfulness score is a teaching simplification, not the exact RAGAS claim-level metric.
4. Narrow the delimiter wording in `Lecture/lectures/lec008.html`.
5. Remove the `\s` docstring warning in `EXER020/starter/ingest.py`.

### Add next

1. Offline course-check GitHub Actions workflow.
2. Authentication, authorization, and tenant-isolation lesson.
3. Production load, backpressure, SLO, and graceful-shutdown lab.
4. Larger categorized capstone evaluation with a held-out subset.
5. Release-gated evaluation workflow.
6. Privacy and data-lifecycle lesson.
7. Prompt and prefix caching lesson.

### Keep optional

- fine-tuning and LoRA;
- model-serving internals;
- quantization;
- audio and real-time interfaces;
- managed-cloud deployment walkthroughs.

---

## Final verdict

The course is technically thoughtful, coherent, and substantially better than a typical LLM framework tour. It teaches learners to inspect abstractions, measure behaviour, constrain agents in code, evaluate retrieval separately from generation, and acknowledge unresolved security risks.

Its main limitation is scope: it reaches a containerized **production-style prototype**, not a production service. The existing material is honest about that. The highest-value next step is therefore not more agent patterns; it is an additional production track covering identity, tenant boundaries, operational load, privacy, and release-gated evaluation.
---

## 7. Validation of this review (2026-11-15)

Every finding above was checked against the working tree before anything was planned. **All of them hold.** Two need a correction, and three structural suggestions were accepted in a different form.

### Findings checked

| Finding | Result | Evidence |
|---|---|---|
| 41 lectures, 41 exercises, 246 Python files | Confirmed | counted |
| 41 quizzes, 170 questions, all well formed | Confirmed | `check_quizzes.py` passes |
| Shutdown claim in Lecture 041 | Confirmed, and worse than stated (see below) | `lec041.html:83`, `EXER041/solution/service.py` catches only `KeyboardInterrupt` |
| "Reasoning before score improves judgments" | Confirmed as an unqualified claim | `lec024.html`, LLM-as-judge list |
| 1–5 faithfulness score vs the RAGAS definition | Confirmed | the lecture cites the claim-level definition; `EXER024/solution/evaluate.py` asks for one 1–5 score |
| Delimiters "help against injection" | Confirmed | `lec008.html:37` |
| `\s` warning in `EXER020/starter/ingest.py` | Confirmed | the `load_html` docstring; the solution uses a raw string and is fine |
| No CI workflow runs the checks | Confirmed | `.github/workflows/` holds only `pages.yml`; the README calls `--offline` the CI command |
| Capstone evaluation is 8 cases with an 80% bar | Confirmed | `EXER037/eval_set.json`, `EXER037/README.md:50,60` |
| Service limits (client-chosen `thread_id`, no auth, 300 s timeout, truncated bodies) | Confirmed | `service.py:112,145,151` |

### Corrections to the review

1. **The shutdown problem is larger than section 2 says.** The review states that the default response to `SIGTERM` is process termination. That is true for an ordinary process, but the service runs as process 1 in the container, and the kernel does not deliver a signal to process 1 unless that process installed a handler for it. Python installs one for `SIGINT` only. So `docker stop` is ignored for the 10-second grace period and then the container is killed. The fix is still the one proposed: reword now, and install a `SIGTERM` handler in the load lesson.
2. **Topics the review lists as absent are partly present as mentions.** Idempotency, p95 latency, PII and prompt versions each appear in one or two lectures or stretch goals. None is built or checked, so the gap stands; the new lessons should link back to those mentions.

### Structural suggestions: accepted in a different form

| Suggestion | Decision | Reason |
|---|---|---|
| Rename Module 8 | Accepted: "Evaluation, Context and Deployment" | A rename touches four files and no numbers |
| Move EXER038 before EXER037 | Not renumbered | EXER041 and an EXER038 stretch goal import EXER037 by path. The capstone evaluation gets an in-order tool check and a pointer to Lecture 038 instead |
| Split Lecture 040 | Not split | It would move Deploying the Capstone to a third number in two days. The estimate goes from 75 to 105 minutes |
| New lessons | Appended as EXER042–049, Module 9 | Each one depends on EXER041 or earlier, so appending keeps the prerequisite order and EXER001–041 keep their numbers |

The resulting plan and the checklist are in [Plan.MD](Plan.MD), section 8.

---

## 8. Further topics worth adding

These are additions to section 5, found while validating. Coverage was checked by searching all lectures and exercise READMEs.

### Added to the plan as lessons

#### Safe side effects (EXER043)

EXER011 teaches retries and EXER029 teaches approval, but nothing teaches what happens when a tool that changes something runs twice. A retried request, a resumed checkpoint or a crash between "refund issued" and "result saved" all repeat the call. Idempotency is mentioned in two lectures and never built.

A lesson should cover idempotency keys, at-least-once execution, what LangGraph replays on resume, and an audit record per side effect.

> Kill the agent in the middle of a refund tool, resume it, and prove from the audit log that the customer was refunded once.

This ranks beside identity in priority: it is the other way a helpdesk agent loses real money.

#### Learning from production (EXER049)

The course builds evaluation sets by hand and never shows where new cases come from once users arrive. EXER025 has a thumbs up/down stretch goal and EXER035 records traces; nothing joins them.

A lesson should cover collecting explicit and implicit feedback, sampling traces for review, turning a failure into a regression case, and watching quality and cost drift between releases. It closes the loop that release-gated evaluation (EXER048) opens.

### Folded into lessons already proposed

| Topic | Goes into | Why it matters |
|---|---|---|
| Permission-aware retrieval | Identity (042) | Binding threads to a user is not enough if the vector store returns documents that user may not read. Filter by access metadata at query time, not after generation |
| Per-user quotas and token budgets | Load (044) | A rate limit counts requests; one user with long prompts can still spend the whole budget |
| `SIGTERM` handling and HTTP 413 | Load (044) | Both are listed limits of the EXER041 service |
| Batch endpoints for offline work | Caching (045) | Evaluation runs and bulk ingestion do not need an immediate answer and cost roughly half as much through a batch endpoint, where the provider offers one |
| Model retirement and upgrades | Model selection (046) | Hosted models are withdrawn on a schedule. Re-running the evaluations against the replacement is the most common reason a team needs the comparison harness |
| Prompts as versioned artifacts | Release gates (048) | A baseline is meaningless unless it names the prompt version it was measured with |

### Worth a stretch goal, not a lesson

- **Streaming from the deployed service.** Lecture 007 streams to a terminal and Lecture 015 to Streamlit; `/ask` in EXER041 returns one JSON body. A server-sent-events endpoint is a good stretch goal for EXER041.
- **A read-only database tool.** Querying structured data is a common agent task and absent from the course: a SQL tool with a read-only role, parameterized queries and a row limit. Fits as a stretch goal of EXER018 or EXER034.
- **OpenTelemetry export.** Lecture 035 builds its own tracker and names OpenTelemetry once. Exporting the same spans in the standard format is a natural second stretch goal there.
- **Hard documents.** Tables, scanned pages and images inside PDFs are where real ingestion fails. One stretch goal in EXER020 that measures retrieval on a table-heavy document would show the problem without a full lesson.

### Considered and left out

- **Automated red-teaming.** Lecture 036 already has learners write attacks and is honest that the problem is unsolved; a generator of attacks adds volume, not understanding.
- **More agent patterns** (planning, reflection, swarm variants). The review's verdict is right: the gap is production practice, not agent shapes.
- **Agent-to-agent protocols.** Module 6 covers MCP in three lessons; a second protocol would be a tour, not engineering.

### Revised "add next" order

1. Corrections A1–A5 and the offline CI workflow.
2. Identity and tenant boundaries (042).
3. Safe side effects (043).
4. Operating under load (044).
5. Categorized capstone evaluation with a held-out subset, then release gates (048).
6. Caching (045), model selection (046), privacy (047).
7. Learning from production (049).
