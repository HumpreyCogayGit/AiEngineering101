# AI Engineer Course — Extended Plan

**Status: all four phases are built** (2026-11-14). This file is kept as the record of what was
planned, what was decided, and where the result differs from the plan. [Plan.MD](Plan.MD) describes
the course as it now exists.

| Phase | Deliverable | Built |
|---|---|---|
| A | Self-check quiz on every lecture page | 40 quizzes, 166 questions, `check_quizzes.py` |
| B | Stretch goals in every exercise README | 40 exercises, 2 goals each, with reference code in `EXERnnn/stretch/` |
| C | Deeper Concept sections | A worked example from captured output in lectures 016–031 |
| D | New topics | EXER038–040 and their lectures, as Module 8 |

## Decisions made

The four open questions at the end of this file were answered before the work started:

1. **Quiz format:** multiple choice only.
2. **Quiz score:** shown on the home page, beside each lecture.
3. **Stretch goal solutions:** reference code for every goal, in a `stretch/` folder per exercise.
   This replaces the "no reference solutions" rule in Phase B below.
4. **Phase D:** in scope, all three exercises.

## Where the result differs from the plan

- **Stretch goals have reference code** (decision 3). It imports the reference solution through
  `aicourse.stretch.solution_module()` and never changes it, so every `check.py` is unaffected by
  construction. The reference code of every goal was run once; it is not part of `check_all.py`, because most
  call the live model.
- **A few goals were adjusted while building them:**
  - 001 goal 1 needs one HTTP request, which is taught in EXER003. The README says so.
  - 023 goal 2 keeps its five questions in `EXER023/stretch/hard_questions.json`, not in
    `data/eval_questions.json`, because other exercises' checks depend on that file.
  - 026 goal 2: LangGraph renders PNGs through the public mermaid.ink service. The reference script
    writes the Mermaid text by default and only calls the service with `--png`. The PNG in the README
    was rendered locally.
  - 032 goal 2 connects to the EXER033 notes server by default (already on disk); a public server is
    an optional command-line argument.
  - Names follow the provider-neutral rule: "embedding model", not "embedding deployment".
- **Phase C** added one `Worked example` subsection at the end of each Concept section (300–450 words),
  for all three groups in the plan: RAG (019–025), agents (026–031) and tools (016–018).
- **Phase D exercises follow the full layout**, including a quiz and two stretch goals each, so the
  totals are 40 quizzes and 80 stretch goals rather than 37 and 74.
- **One bug in existing code was fixed on the way:** `UsageTracker` in EXER035 was an unhashable
  dataclass and crashed when passed into nested graphs (found by 031 goal 2). It is now `@dataclass(eq=False)`.
- **One addition to the shared package:** `aicourse.settings.settings_from_environment()`, used by EXER040.

## How it was verified

- `uv run python check_all.py` on the hosted provider: 40/40 exercises (every solution passes, every
  untouched starter fails) and 166 quiz questions valid. EXER038–040 also pass on Ollama (`gemma4:e4b`).
- Every stretch goal's reference code was run once on the hosted provider. The five Streamlit stretch
  apps were run headless (`streamlit.testing`) against the live model.
- EXER040: the image was built and the container run; it reported `healthy`, ran as a non-root user,
  held no `.env`, and answered a question.
- The Further Reading links of lectures 038–040 were checked and answer.
- **Not run:** two paths that reach outside the machine: `EXER026/stretch/goal2_graph_png.py --png`
  (sends the diagram text to mermaid.ink) and `EXER032/stretch/goal2_second_server.py npx …` (downloads
  and starts a public MCP server). Both are optional arguments; the default paths of both scripts were run.
- **Not done:** a full live run of exercises 001–037 and of the stretch code on Ollama.

The original plan follows, unchanged except for this status section.

## Phase A — Self-check quizzes

**Purpose.** A learner finishes the lecture and can tell, in two minutes and before opening
the exercise, whether the concept landed. The quiz is for the learner, not a grade.

**Design**

- 4 questions per lecture (5 for the longer ones: 009, 011, 023, 024, 029, 036).
- Multiple choice, one correct answer, three plausible wrong ones. Each wrong answer is a
  real misconception, and choosing it shows a one-sentence explanation of why it is wrong.
- Questions test understanding and prediction ("what happens if…"), not recall of names.
- At least one question per quiz is drawn from that lecture's Common Pitfalls.
- No model calls and no network: the quiz works offline and from `file://`, like the site.

**Where it lives**

- A tenth section, **Check Yourself**, between Discussion and Further Reading. Plan.MD's
  "nine sections" rule becomes ten.
- Questions are data, not markup: `Lecture/assets/js/quizzes.js` holds
  `window.QUIZZES = { 4: [ {q, options, answer, why}, … ], … }`, and `app.js` renders it.
  Adding or fixing a question never touches a lecture page.
- Score is stored in the browser next to the existing "completed" state, and the home page
  shows it beside each lecture. "Mark as complete" stays manual; a low score never blocks it.

**Definition of done**

- Every lecture has a quiz, and every question has exactly one correct answer and a `why`
  for each wrong option.
- A script (`check_quizzes.py`, run by `check_all.py`) validates the data: 37 lectures
  covered, 4 options per question, answer index in range, no empty explanations.
- Each question is answerable from its own lecture page alone.

**Quiz focus per lecture**

| # | The quiz checks that the learner can… |
|---|---|
| 001 | say why keys live in `.env`, what a deployment name is, and what `uv run` does |
| 002 | read a nested response safely and predict what Pydantic rejects |
| 003 | place the key, the model and the messages in a raw request, and read a 401 vs a 429 |
| 004 | predict the effect of temperature and of a small output cap; tell classic from reasoning models; estimate a cost |
| 005 | explain why the model "forgets" and what is actually sent on turn two |
| 006 | shape a text-plus-image message and choose what to trim first |
| 007 | assemble a reply from deltas and explain time to first token |
| 008 | choose between instructions and few-shot examples, and spot test-set leakage |
| 009 | choose JSON mode vs structured output, and say what the repair loop sends back |
| 010 | pick an exit code, and tell stdin input from an argument |
| 011 | decide which errors to retry, and why backoff needs jitter |
| 012 | map each LangChain call to its raw equivalent; choose `.text` over `.content` |
| 013 | trace data through a pipe and predict what each step receives |
| 014 | say what `with_structured_output` returns and when validation fails |
| 015 | predict what a Streamlit re-run keeps and what it loses |
| 016 | order the messages of a tool round trip, and say who executes the tool |
| 017 | handle several tool calls in one reply, and say where a tool error goes |
| 018 | rank the shell safeguards by what each one actually prevents |
| 019 | interpret a cosine score and say why scores from two embedding models cannot be compared |
| 020 | predict the effect of chunk size and overlap on retrieval |
| 021 | explain why a second ingest adds nothing, and when to use a metadata filter |
| 022 | say what makes an answer grounded and when the chain must refuse |
| 023 | match each retrieval technique to the weakness it fixes; read hit rate @1 vs @4 |
| 024 | tell retrieval metrics from answer metrics, and name a limit of LLM-as-judge |
| 025 | explain why a follow-up question must be rewritten before retrieval |
| 026 | predict a state update with and without a reducer |
| 027 | say what ends the agent loop and what the recursion limit protects against |
| 028 | tell thread memory from long-term memory and say what `thread_id` selects |
| 029 | say what state an interrupt saves and what resume replays |
| 030 | route a question, and explain why out-of-scope questions still go to retrieval |
| 031 | choose between supervisor, handoff and a single agent; say which rules belong in code |
| 032 | tell hosts, clients and servers apart, and tools from resources from prompts |
| 033 | say what the model sees of a tool, and how a tool should report an error |
| 034 | explain tool namespacing and why a missing tool is a security control |
| 035 | read a trace timeline and find where the tokens went |
| 036 | name the layer that stops a given attack, and say why a strong model is not a guardrail |
| 037 | justify each design choice of the capstone against the rubric |

## Phase B — Stretch goals

**Purpose.** A learner who finishes early has somewhere to go, and a learner repeating the
course has something new. Stretch goals are optional and never required for "complete".

**Design**

- Two per exercise, under a **Stretch goals** heading at the end of the README, after the
  success criteria. The same list appears at the end of the lecture's Walkthrough.
- Goal 1 extends the exercise's own concept. Goal 2 connects it to an earlier or later
  exercise.
- Each goal states an observable result, so the learner knows when it is done.
- No reference solutions and no automated checks. The existing checks must still pass
  after a stretch goal is done; goals that would break them are rejected.
- Three exercises already have stretch goals (003, 005, 033). They are rewritten to this format.

**Definition of done**

- Every README has two stretch goals in the format above.
- Each goal was done once by hand against the reference solution, to confirm it is
  achievable with what the course has taught by that point and that the checks still pass.

**Stretch goals per exercise**

| # | Goal 1 (extend) | Goal 2 (connect) |
|---|---|---|
| 001 | Make `check_setup.py` report the embedding deployment as reachable or not | Print which settings came from `.env` and which from the environment |
| 002 | Add a `tool` role to the message model, with its required id field | Validate `sample_response.json` with a Pydantic model of the whole response |
| 003 | Send a second request with a system message and compare token usage | Print the rate-limit headers of the response |
| 004 | Add `reasoning_tokens` to `CompletionResult` when the model reports them | Price the same prompt for two models from a small price table |
| 005 | Add a `/save` command that writes the conversation to JSON, and `/load` | Show the running token count in the prompt (EXER004) |
| 006 | Send two images in one message and ask for the differences | Trim by summarizing the dropped turns instead of deleting them |
| 007 | Stop the stream cleanly on Ctrl-C and keep the partial reply | Stream tool-call deltas and assemble the arguments (prepares EXER016) |
| 008 | Add a fourth prompt version that explains its label, and measure it | Print a confusion matrix of labels, not only accuracy |
| 009 | Add a nested model (an `Address` inside `Event`) and extract it | Count how often the repair loop is needed over 20 runs |
| 010 | Add a `--json` flag that prints a machine-readable result | Add a `classify` command that reuses the EXER008 prompt |
| 011 | Add a circuit breaker: stop calling after N consecutive failures | Run the EXER008 evaluation concurrently and report the speed-up |
| 012 | Add `astream` and print two answers interleaved | Swap in the fake chat model and run your chatbot offline |
| 013 | Add a third step that scores the translation, as a parallel branch | Add a fallback chain for when the summary is too long |
| 014 | Make the parser return a list of validation problems instead of raising | Parse the invoices concurrently with `batch` (EXER012) |
| 015 | Add a "regenerate" button for the last answer | Show token usage per message in the sidebar (EXER004) |
| 016 | Add a `get_time(timezone)` tool and a question that needs two different tools | Run the tool calls of one round concurrently (EXER011) |
| 017 | Bind with `parallel_tool_calls=False` and compare the message trace | Give `convert_currency` a Pydantic `args_schema` with a currency enum |
| 018 | Add a dry-run mode that explains each command without running it | Log every command, decision and exit code to a JSONL audit file |
| 019 | Embed in batches and cache vectors on disk by text hash | Plot the similarity matrix of the sentences as a heat map |
| 020 | Add a Markdown-header-aware splitter and compare its chunks | Record the heading path of each chunk in its metadata (used in EXER022) |
| 021 | Delete and re-ingest one changed document without touching the others | Compare cosine and L2 distance on the same queries |
| 022 | Return the exact quoted sentence that supports each citation | Stream the answer and print the sources at the end (EXER007) |
| 023 | Add MRR as a second metric beside hit rate | Add five harder questions to the eval set that separate the strategies at @4 |
| 024 | Run the judge twice per row and report how often it disagrees with itself | Evaluate the best EXER023 retriever and compare both reports |
| 025 | Let the user remove one uploaded file from the index | Add a thumbs up/down per answer and write the feedback to a file |
| 026 | Add a node that asks the user for missing information, with a loop back | Draw the graph to a PNG and add it to the README |
| 027 | Add a per-run tool budget: stop after N tool calls | Stream the agent's tokens as well as its steps (EXER007) |
| 028 | Summarize old turns into one message when the thread grows long | List and delete a user's long-term memories with a small CLI |
| 029 | Require approval only for refunds above a threshold | Persist the pending approval so the script can be closed and resumed (EXER028) |
| 030 | Add a hallucination check on the generated answer before returning it | Score the graph on the EXER024 evaluation set against the plain chain |
| 031 | Add a reviewer agent that can send the draft back to the writer once | Count model calls and tokens for supervisor vs handoff (EXER035) |
| 032 | Read the server's prompt and use it as the agent's system prompt | Connect to a second public MCP server and list its capabilities |
| 033 | Add an `update_note` tool with partial updates | Add a resource that lists all notes, and use it from the EXER032 client |
| 034 | Give the agent the delete tool behind an approval step (EXER029) | Add a third server and resolve a tool-name collision |
| 035 | Add latency percentiles (p50, p95) per tool to the report | Export the spans as JSON and render the timeline in Streamlit (EXER015) |
| 036 | Write two new stealthy attacks and say which layer stops each | Add an output check that catches a secret spelled backwards or spaced out |
| 037 | Add one new tool and two evaluation cases that need it | Add the EXER035 tracker and report the cost of the evaluation run |

## Phase C — Deeper Concept sections (optional)

The lectures are roughly 600–1,700 words each. Twenty-two now show a real sample run, but the Concept
sections themselves are brief. Deepen in this order, because the concepts compound:

1. **Module 4 (RAG, 019–025):** one worked example per lecture that follows a single
   question from query to chunks to prompt to answer, with the actual intermediate values.
2. **Module 5 (agents, 026–031):** a state table per lecture showing the state after each
   node for one run.
3. **Module 3 (tools, 016–018):** the full message list of one tool round trip, annotated.

Target: 300–400 added words per lecture and no new sections. Done when each of these
lectures has one worked example built from captured output, not invented values.

## Phase D — New topics (optional)

| # | Title | The learner builds | Why it is missing today |
|---|---|---|---|
| 038 | Evaluating Agents | A scorer for tool-call trajectories: right tools, right order, right arguments | EXER024 scores RAG answers only; nothing scores what an agent *did* |
| 039 | Conversation Memory Strategies | Trimming vs summarizing vs retrieval over past turns, compared on cost and recall | EXER006 and EXER028 trim; summarization is only a stretch goal |
| 040 | Deploying the Capstone | The EXER037 app in a container, with settings from the environment and a health check | Plan.MD lists deployment as out of scope, to be added after the capstone |

These would form a Module 8. Each follows the existing exercise layout and definition of done.

## Decisions to make before starting (answered above)

1. **Quiz format:** multiple choice only (planned above), or also short "predict the output"
   questions with a reveal button?
2. **Quiz score:** shown on the home page (planned above), or kept private to each lecture page?
3. **Stretch goal solutions:** none (planned above), or a `stretch/` folder with reference code?
4. **Phase D:** in scope at all, and if so, which of the three first?
