# Helix Under the Hood — Copilot Prompt Pack

Oct 19, 2026 · @Pranay

## How to use this pack

Run one prompt at a time in Copilot Chat (Agent mode). Each prompt writes one .md file into a local `helix-study/` folder, which you read in VS Code's Markdown preview.

**Why Copilot's output was vague before**

- "Give me a 15,000 ft view" asks for a summary, so the model writes general filler.
- Nothing forced it to open files or cite them, so it guessed from file names.
- There was no fixed shape, so every answer had a different structure and harder words.

These prompts fix all three. Each one asks specific interview questions, demands a file reference for every claim, and follows one shared style file. The style file builds each topic from the simplest idea upward and holds numbers back until the idea is clear.

**Setup (once)**

1. In the repo root, create a folder `helix-study/`.
2. Keep it out of git, locally only: `echo "helix-study/" >> .git/info/exclude`
3. Create `helix-study/STYLE.md` and `helix-study/FACTS.md` and paste in the blocks from the next two sections.
4. In Copilot Chat, switch to **Agent** mode so it can open files and write the .md file.
5. In the model picker, choose the strongest model available to you.
6. If `#file:` does not attach a file, type `#` and pick the file from the list.
7. If Mermaid diagrams show as code, install the "Markdown Preview Mermaid Support" extension.

Paths come from your folder screenshots. Where a name was cut off, the prompt uses `*` and Copilot searches for it. The notes contain internal design details, so keep `helix-study/` on the work laptop.

**Run order**

| # | Output file | Topic | Model and effort | Priority |
| --- | --- | --- | --- | --- |
| 00 | 00-big-picture.md | What Helix is, every service, one case end to end | — | Done |
| 00T | 00t-temporal-primer.md | Temporal from zero, using Helix's real Temporal code | Sonnet, medium | Done |
| 01 | 01-orchestration.md | Orchestrator and human gates: design vs built | Opus, high | Must, next |
| 02 | 02-agents-layer.md | Inside an agent, registration, handoff, contracts | Opus, medium | Must |
| 04 | 04-failure-recovery.md | Failure scenarios in code and design | Opus, medium | Must |
| 13 | 13-llm-layer.md | Models, prompts, UAIS, quality measurement | Opus, medium | Must |
| 07 | 07-deploy-scale.md | Helm, KEDA, cells, Azure services, load tests | Sonnet, medium | Must |
| 15 | 15-tradeoffs.md | All 33 ADRs, the review, open decisions | Sonnet, high | Must |
| 09 | 09-operations.md | Observability, audit, CI/CD, supply chain | Sonnet, medium | Should |
| 10 | 10-security.md | Policy service, brokers, tokens, PHI | Sonnet, medium | Should |
| 12 | 12-catalog-vendors.md | Registry, version pinning, vendor kit | Sonnet, medium | If time |
| 16 | 16-cheat-sheet.md | Pitch, hardest questions, do-not-claim list | Opus, medium | Must, last |

The old prompts 03, 05, 06, 08, 11 and 14 are merged into the ones above, or already covered by 00.

**For every topic file**

1. Run the topic prompt.
2. Run the fact-check prompt (last section) only if you will quote numbers from that file.
3. Read it top to bottom. Stop at the first part you don't understand and use the follow-up prompt on that one piece.
4. If Copilot stops halfway, say: `Continue. Write the missing sections.`

Agent mode shows every file change for you to keep or undo. Accept only changes inside `helix-study/`.

**Saving Copilot credits.** Copilot now bills by tokens, at a different rate per model, so both the model and the effort level change the cost.

- Start a new Copilot chat for every prompt. A long chat resends its whole history on every turn.
- Use Opus for the five files you must know cold: 01, 02, 04, 13 and 16. Use Sonnet for the rest; 00T showed it reads and summarises well at a much lower cost.
- FACTS.md replaces rediscovery: each prompt lists exact files, so Copilot does not explore the repo.
- Send each finished file to the Claude chat. I check it against FACTS.md and catch errors at no Copilot cost, so you rarely need the fact-check prompt.
- When a section is unclear, ask in the Claude chat, not Copilot.

## STYLE.md — the rules every output follows

Version 2.1: lean shape, token rules that point to FACTS.md, and one-line \[IDEA\] notes in section 9 on how each weak point could be done better. I check those ideas and move the good ones into the TransQA Mini plan. Replace your `helix-study/STYLE.md` with this block.

```text
# Writing rules for Helix study notes (v2.1 - lean)

## Reader
- Me: a senior AI/ML engineer preparing for interviews. English is my second language.
- After reading, I must be able to explain this out loud to a CTO.

## Language
- Simple English. Sentences under 20 words. Active voice.
- Define a technical term in one plain line the first time it appears,
  unless helix-study/FACTS.md already uses it.
- Do not use: robust, seamless, leverages, facilitates, ensures, comprehensive,
  scalable, efficient, various, handles, manages, powerful, flexible -
  unless the same sentence says HOW, with a file reference.

## Truth rules
- Facts in helix-study/FACTS.md are verified. Reuse them. Do not re-verify them.
- Read only the files and line ranges a question needs. Never answer from file names.
- Every new factual claim ends with evidence: path/to/file.py:L120-L145 or a doc path.
- Tags: [CODE] seen in code or config; [DOCS-ONLY] only in docs, specs or ADRs;
  [NOT FOUND] searched, absent; [CONCEPT] general knowledge, not about this repo;
  [IDEA] your opinion on a better design - only in section 9, never mixed into facts.
- Never invent numbers, names or settings. When docs and code disagree, show both.
- Describe what Helix does as it is, even when it looks wrong. Put judgement in [IDEA].

## Token rules
- No text before section 1. No closing summary.
- Do not repeat content from other helix-study files; write "see 00 section 5".
- Temporal concepts are explained in helix-study/00t-temporal-primer.md.
  Do not re-explain them; write "see 00t part 7".
- Code snippets: max 15 lines each, max 4 per file.
- If an answer is [NOT FOUND], say so in one line and move on.

## Shape of every file
1. One-line answer.
2. Altitude 30,000 ft: 3-5 sentences, no technical terms, no numbers.
3. Why it is built this way: start from the naive design, say why it breaks,
   then add each piece and the problem it solves. Cite ADRs.
4. Altitude 10,000 ft: each component as What / Why / How, 2-4 lines each.
   Mark each one built / stub / schema only / designed only.
5. Altitude 1,000 ft: numbered steps for ONE real example, with real field names.
   Tag each step [CODE] or [DOCS-ONLY].
6. Diagram: one Mermaid diagram, max 12 boxes, plain labels.
7. Code walkthrough: the most important snippets, important lines explained.
8. Exact settings: table Setting | Value | File. New values only.
9. Weak points and better options: each weak point in one line with evidence,
   then one line starting [IDEA] on how it could be done better. Max 8.
10. Interview Q&A: answer every question in the prompt, 3-6 sentences each,
    one file reference each. Then 2 CTO follow-ups for the whole file, with answers.
11. Glossary: new terms only, max 12.
12. Files read: one comma-separated line.

## Hard limits
- Write only inside helix-study/. Do not edit, create or delete any other file.
- Do not install, deploy or run git commands. Small read-only Python checks are allowed.
- If the output gets long, write it section by section until all 12 sections exist.
```

## FACTS.md — what 00 already proved

Paste this into `helix-study/FACTS.md`. It holds everything 00 verified, with exact paths, so later prompts read only what they still need. Update it as each new file adds facts.

```text
# Helix facts - verified in 00-big-picture.md and 00t-temporal-primer.md
Treat these as known. Do not re-read files just to re-confirm them.
Read a listed file only when a question needs a detail that is not here.
Temporal concepts are explained in helix-study/00t-temporal-primer.md.

## Build status
Built:        trigger_intake_svc, trigger_gateway_svc, cell_router_svc (bugs), registry_svc,
              identity_policy, trust_boundary/memory_broker, libs/*, agents/ worker
Stubs inside: intake AV scan, in-memory blob store, PHI key, dedup, case-id counter,
              capability-token minting
Schema only:  orchestrator_svc (cases, effect_ledger), gate_svc (gates, decisions),
              audit_svc (audit_log, outbox), trust_boundary/phi_broker
Empty:        review_console_svc, connector_broker, llm_broker, agent_sandbox_adapter,
              services/tests/e2e
NOT FOUND:    production @workflow.defn (GenericOrchestratorWorkflow has no worker),
              code reading MCS_workflow_config_v1.json, .proto / gRPC, outbox poller,
              Lane A consumer, Registry /triggers route, Cell Router /start route,
              workflow patching, continue-as-new

## Real request path today
POST /intake -> Service Bus triggers-queue (session_id = case_id) -> Trigger Gateway
-> Registry GET /triggers/{wf} (404 -> dead-letter rejected_allowlist)  <- flow stops here
-> Cell Router POST /start (missing) -> workflow_directory row
-> start GenericOrchestratorWorkflow on orchestrator-platform (no worker)
Cell Router bugs: NameError consumer/intake.py:L182-L183; Registry path /api/v1 mismatch;
start call bugs - see "Cell Router start method" below.

## Where Temporal is used in code
Start:   services/cell_router_svc/src/cell_router_svc/store/temporal_client.py:L67-L70, L106-L200
         services/cell_router_svc/src/cell_router_svc/consumer/intake.py:L177-L187, L236-L268
Signal:  services/trigger_gateway_svc/src/trigger_gateway_svc/dispatch/signal_dispatch.py:L42-L57
         services/trigger_gateway_svc/src/trigger_gateway_svc/store/workflow_client.py
         signal name trigger:<step> (services/libs/helix_trigger_lib/src/helix_trigger_lib/route.py:L32-L34)
Worker:  agents/src/agents/worker.py:L1-L94; agents/src/agents/registry.py:L9-L49
Wrapper: services/libs/helix_platform_libs/src/helix_platform_libs/agent_activity/
         wrapper.py:L1-L136; envelope.py:L49-L113; broker_clients.py:L22-L115
Only runnable workflows (tests / perf):
         agents/tests/activity/_dummy_chain_probe_workflow.py:L9-L33
         agents/tests/activity/test_dummy_agents_worker_e2e.py:L16-L42
         agents/src/agents/perf/probe_workflow.py, agents/src/agents/perf/load_test.py:L50-L70
Local:   services/docker-compose.yaml:L11-L42 (temporalio/auto-setup :7233, UI :8233)
Scaling: infra/helm/agents-worker/values.yaml, templates/scaledobject.yaml

## Temporal details
Activity registration: @agent_activity -> temporalio.activity.defn(name=agent_id)
  (wrapper.py:L36-L45, L136). Bad input -> failed_envelope "VALIDATION_ERROR" (L106);
  core_fn runs with BrokerError uncaught, so Temporal retries it (L112).
Heartbeat: only reasoning_loop agents call heartbeat({"iteration", "note"})
  (wrapper.py:L55-L72); single-shot agents use a no-op (L49-L53). Wired when the
  first loop agent (logo-agent) is ported.
Worker: TEMPORAL_NAMESPACE default "default" (worker.py:L21); CORE_AGENTS_QUEUE_CLASS
  all | deterministic | llm picks the queues (L33-L40); one Worker per queue via
  asyncio.gather (L83-L86); production = one Deployment per class, "all" is for dev (L1-L6).
  registry.py "dummy" profile registers only the two dummy agents (L15-L22).
Test chain: DummyChainProbeWorkflow, id probe-dummy-chain-wf, queue core-agents-deterministic,
  start_to_close 30 s per activity (_dummy_chain_probe_workflow.py:L16, L27) - the only
  timeout in code; WorkflowEnvironment.start_local() (test_dummy_agents_worker_e2e.py:L18).
Cell Router start method (temporal_client.py:L106-L200): named start_workflow but calls
  execute_workflow (blocks up to the 30-day run timeout); TypeError from workflow= plus a
  positional input; wrong keyword workflow_id_reuse_policy (Python SDK: id_reuse_policy);
  comment L185-L186 wrongly says it returns a handle, so run_id at L187 would be empty.
  Correct parts: REJECT_DUPLICATE default (L112, L163-L164), deterministic ID (L125-L130),
  WorkflowAlreadyStartedError treated as success (L116-L120, L195-L197).
Signal: Gateway raises NoLiveRun when the Directory row is missing or status != "open"
  (signal_dispatch.py:L43-L49) -> dead-letter rejected_no_run; else it signals the run_id
  stored in the row (L51-L57). A dehydrated case therefore fails closed.

## Key values
case_id case_<YYYY>_<MM>_<DD>_<NNNNN>; workflow_id {tenant_id}:{workflow_type}:{case_id}
Reuse policy REJECT_DUPLICATE; workflow execution and run timeout 30 d; task timeout 10 min
Queues: core-agents-deterministic (8 activities, 32 threads), core-agents-llm (2, 64 threads)
Worker graceful shutdown 30 s
KEDA: metric temporal_activity_task_queue_backlog; deterministic min 1 max 40 threshold 10;
      llm min 1 max 60 threshold 5; polling 30 s; cooldown 300 s
Designed retry (docs only, docs/AGENT_INVOCATION_UNIFIED_FLOW.md Phase 2): initial 1000 ms,
      backoff 2.0, max attempts 3, start-to-close 60000 ms, heartbeat 30000 ms
MCS SLA: end_to_end 1440 min, per_step 480 min. Max upload 25 MiB.
Designed scale: 1B+ runs/year, ~32 starts/s average; p95 < 2 s deterministic step,
      < 8 s AI step.

## Design decisions already summarised (00t part 10)
Spec 2.2: open runs, not start rate, size storage (Little's Law); Cassandra history plus a
  visibility store; long-dwell gates dehydrate (spec 6.8); Continue-As-New does not reduce
  open-run count. Spec 5.3 covers context building and determinism.
ADR 0011: an agent is one activity; its loop is bounded by max_iterations with read-only
  tools, so a crash restarts the whole loop safely; revisit with a child workflow if loops
  threaten the 8 s p95.
ADR 0019: workflow state holds only opaque case-scoped references plus non-PHI metadata;
  agents redeem references at a broker in their own pod; cost = one extra broker call per
  PHI field.

## Agent result envelope
{status: success | needs_gate | failed, result, produces_artifacts, gate_signals,
 confidence, errors, sla, audit_entry}
Business failures are RETURNED as failed envelopes (Temporal sees success, no retry).
Broker errors are RAISED (Temporal retries). needs_gate = any gate signal present.

## MCS workflow (services/MCS_workflow_config_v1.json, config only, nothing reads it)
detect-lang-agent -> segmentation-agent -> validation-agent -> annotate-agent
wired by input_bindings.*.producer; annotate-agent hitl_enabled, SLA 1-4 h, escalation 0.5 h.
Domain: regulated English<->Spanish CMS member materials; MCS = human translation
function (ADR 0007).

## Docs vs code
Start hop: gRPC in ADR 0031, HTTP /start in code; neither exists.
Task queues: {cell_id}:{tenant_id}:activities in docs; orchestrator-platform and
core-agents-* in code. AGENTS.md section 5 is out of date.
File paths in docs/AGENT_INVOCATION_UNIFIED_FLOW.md are pseudo-code.

## Delivery
Helm charts: identity-policy, agents-worker only.
CI: identity-policy (3 workflows), trigger-gateway (2), trigger-intake (2).
No CI for agents, registry, cell router. No CD.
```

## Corrections to finished files

Copilot's outputs are mostly accurate, but each has a few errors. Fix these in your files, or at least remember them before an interview.

**00-big-picture.md**

- Q1 says "10+ workflow runs per year". The spec figure is 1B+, as section 8 of the same file states.

**00t-temporal-primer.md**

- Part 8 is cut off mid-sentence, and its second half sits under a duplicate "## 9" heading. Rename the first "## 9" to "## 8 (continued)". The missing reference: the signal name `trigger:<step>` is built in `services/libs/helix_trigger_lib/src/helix_trigger_lib/route.py:L32-L34`.
- Part 11, check 4 is wrong once the run has finished. Temporal's default reuse policy is ALLOW\_DUPLICATE, so starting `demo-1` again is rejected only while it is still running; after it completes, the same ID starts a new run. `REJECT_DUPLICATE`, which Helix sets, is what blocks that. This is a good interview point.
- Part 6 hedges on the keyword. It is confirmed: the Python SDK keyword is `id_reuse_policy`, so `workflow_id_reuse_policy` is a third bug in the same Cell Router call.

## Prompts 00–02: big picture, Temporal, orchestration, agents

Run these first, in order. 00 is done, and its facts now live in FACTS.md.

### 00 — Big picture (done)

Output: `helix-study/00-big-picture.md`. It found that the orchestrator workflow is designed but not built, and that today's request path stops at the Trigger Gateway. FACTS.md carries the details.

### 00T — Temporal primer (done)

Output: `helix-study/00t-temporal-primer.md`, run on Sonnet. Its new facts are in FACTS.md and its errors are listed under Corrections. The prompt stays here for reference.

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.
Two changes for this file:
- Most of it is general Temporal knowledge. Tag that [CONCEPT]; it needs no file reference.
- Use the 12 parts below instead of STYLE's shape. End with Glossary and Files read.

Topic: Temporal from zero - what it is, how it works, how to use it -
with Helix's real Temporal code as examples.

Read only these files (FACTS.md has the line ranges):
- agents/src/agents/worker.py, agents/src/agents/registry.py
- services/libs/helix_platform_libs/src/helix_platform_libs/agent_activity/wrapper.py
- agents/tests/activity/_dummy_chain_probe_workflow.py
- agents/tests/activity/test_dummy_agents_worker_e2e.py
- services/cell_router_svc/src/cell_router_svc/store/temporal_client.py (L60-L200)
- services/trigger_gateway_svc/src/trigger_gateway_svc/dispatch/signal_dispatch.py
- docs/adr/0011-*.md and docs/adr/0019-*.md (Decision section only)
- docs/spec/2026-09-11-aks-temporal-distributed-architecture-design.md (section 2.2 only)
Do not explore other files.

Each part: one real-life analogy, the plain idea, a tiny Python example
(max 12 lines), then "In Helix:" with file and line, or "In Helix: not built yet".

1. The problem: a 4-step document pipeline crashes at step 3. Without Temporal,
   what breaks: lost progress, duplicate work, hand-written retries, waiting days
   for a human.
2. Durable execution and replay: event history, and how a new worker resumes a run.
   Walk through replay with a small example.
3. Building blocks: Temporal server and its database, namespace, workflow, activity,
   worker, task queue, client, workflow ID, run ID, event history, Web UI.
   One line each, plus where each lives in Helix.
4. Workflow vs activity: determinism rules, what breaks them, one mistake and its fix.
   Why Helix agents are activities and the orchestrator must be a workflow.
5. One run as a Mermaid sequence diagram: client start, server events, worker polls
   the task queue, activity runs, result recorded, next activity.
   Use the dummy chain test workflow as the example.
6. Starting workflows: start_workflow vs execute_workflow, workflow ID reuse policy
   (REJECT_DUPLICATE), idempotency. Use the Cell Router call bug from FACTS.md as a
   teaching example: what is wrong, and what correct code looks like.
7. Failures: schedule-to-close, start-to-close and heartbeat timeouts, retry policy,
   non-retryable errors, heartbeats with progress. Then Helix's choice to RETURN
   business failures as envelopes and RAISE broker errors: what Temporal does in
   each case, and the trade-off.
8. Talking to a running workflow: signals, queries, updates. Helix's trigger:<step>
   signal. How a workflow can wait days for a human, and why Helix designs
   dehydrate/rehydrate instead (section 2.2). Explain Little's Law with the numbers
   in that section.
9. Workers in production: thread pools for sync activities, graceful shutdown,
   one worker per task queue, scaling workers on queue backlog with KEDA
   (values in FACTS.md).
10. Limits and evolution: payload and history size, continue-as-new, why PHI and
    large data stay out of history (ADR 0019), versioning with patching while old
    runs are in flight, agent loops inside one activity (ADR 0011) and what a crash loses.
11. Hands-on for my Mac: the smallest runnable example - one workflow, two activities,
    one retry. Write the exact commands, do not run them: temporal server start-dev,
    uv add temporalio, run the worker, start the workflow. Then what to check in the
    Web UI, and how to kill the worker and watch the run recover.
12. Temporal vs Celery + Redis, Azure Durable Functions, AWS Step Functions, Airflow
    and LangGraph: one table, when each fits. Then 10 interview questions on Temporal,
    basic to hard, 3-5 sentence answers, with Helix examples where they exist.

Write the result to helix-study/00t-temporal-primer.md
```

**Hands-on alongside it:** Temporal's free [Temporal 101 with Python](https://learn.temporal.io/courses/temporal_101/) course (about 2 hours) builds a small app with workflows, activities, the Web UI and failure recovery. Do it on your Mac; it also prepares you for TransQA Mini.

### 01 — Orchestration and human gates: design vs built

No orchestrator code exists, so the design lives in docs, and interviewers will ask how it is meant to work and why. This prompt reads the designs and checks them against what is built. It absorbs the old 05 (human review).

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.
Temporal concepts are in helix-study/00t-temporal-primer.md; refer to them, do not re-explain.

Topic: How Helix is designed to orchestrate one case - the Generic Orchestrator
workflow and human gates - and how much of it exists.

Read:
- docs/spec/*generic-orchestrator-workflow-design* (full)
- docs/implementation/04-generic-orchestrator-implementation.md
- docs/spec/2026-09-11-aks-temporal-distributed-architecture-design.md (sections 5.3 and 6.8 only)
- docs/implementation/case-flow-walkthrough.md (orchestrator and gate steps only)
- docs/spec/*hitl-human-in-the-loop-review-specification* and
  docs/spec/*gate-service-review-console-design* (state machine, SLA, decision flow only)
- services/MCS_workflow_config_v1.json, vendor-kit/schemas/workflow-config.schema.json
- services/orchestrator_svc/src/orchestrator_svc/migrations/versions/ (both files)
- services/gate_svc/src/gate_svc/migrations/versions/ (both files)
- docs/adr/ 0004, 0006, 0012, 0020, 0023 (Decision and Consequences only)
Skip ingress (covered in 00), Temporal basics (00t) and agent internals (02).

Answer:
1. The designed GenericOrchestratorWorkflow, step by step: PinVersions, BuildContext,
   the step loop, gates, completion. Write it as Python-style pseudo-code with real
   Temporal calls (execute_activity, wait_condition, signal handlers), 30 lines max,
   tagged [DOCS-ONLY].
2. Spec 5.3: how context is built and kept deterministic. What is read inside an
   activity, and what is held in workflow state?
3. Walk MCS_workflow_config_v1.json field by field against workflow-config.schema.json.
   Which fields drive execution, and which map to activity options
   (task queue, timeouts, retry policy)?
4. Step order: sequence only, or parallel and conditional through input_bindings?
5. effect_ledger: purpose, columns, and how it gives exactly-once side effects on retry.
6. cases status machine: states, allowed transitions, how the DB trigger enforces them.
7. Gates: when one is raised (needs_gate; gate_type confidence / policy / exception).
   Short wait (timer plus signal) vs long wait (dehydrate, spec 6.8): what decides,
   what is saved, how a fresh run rehydrates, and how the Gateway's NoLiveRun rule
   fits. What happens on SLA expiry and escalation (ADR 0023)?
8. Who decides, how the decision is stored (gates, decisions tables), how the case resumes.
9. ADR 0004 and ADR 0006 in plain words: what they rule out, and why.
10. Why one generic workflow instead of one per use case? What does it cost
    (versioning, testing, debugging)?
11. The smallest set of code needed to run one MCS case end to end, in build order.

Write the result to helix-study/01-orchestration.md
```

### 02 — Agents layer: anatomy, registration, handoff, contracts

The agents worker is the most complete code in Helix, so this is where you can speak from real code. It merges the old 02 and 03.

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.

Topic: The agents layer - inside one agent, how agents are registered and run,
and how data passes between them.

Read:
- agents/src/agents/activities/segmentation_agent/ (all files) - the worked example
- agents/src/agents/activities/logo_agent/activity.py and core/ (the planned first loop agent)
- every other agent: activity.py and contract/ only
- agents/src/agents/io_models/base.py, agents/linguistic-agent-contract.json
- agents/src/agents/legacy_compat/ (first 60 lines of each file)
- services/libs/helix_platform_libs/src/helix_platform_libs/agent_activity/ (all files;
  skip the wrapper.py parts already summarised in FACTS.md)
- agents/tests/contract/ (file names, plus one test in full); agents/tests/unit/ (file names only)
- docs/agents/AGENT_LAYER.md, docs/adr/0012-*.md (Decision only)
- docs/reviews/2026-10-06-core-agents-temporal-framework-review.md (findings list)

Answer:
1. Each part of segmentation_agent (activity.py, core/, data_model/, mappers.py,
   contract/, payload_template.json), and why an agent is split this way.
2. Trace segmentation_agent's payload_template.json from input to output envelope,
   with real field names and one realistic value per field.
3. The wrapper beyond FACTS.md: input model validation, how sla, confidence and
   audit_entry are filled, metrics, the rounding helpers, and the reasoning_loop mode.
4. Table of all 10 agents: queue (deterministic or llm), purpose in one line, input,
   output, LLM used (yes/no), external service called, in the MCS config (yes/no),
   single-shot or reasoning loop. Explain names like bisu and ntdc only if the code does.
5. logo_agent: is it ported? What would its loop look like (max_iterations, tools)?
6. linguistic-agent-contract.json and io_models/base.py field by field.
   Who must follow them?
7. Handoff: what one agent returns and what the next receives - values, paths or
   references? How would input_bindings map to the payload? What is missing
   because no orchestrator exists?
8. Contract versioning and validation: where checked, what happens on a mismatch.
9. Artifacts: produces_artifacts and the write_non_phi_blob passthrough - where do
   files really go today?
10. Tests: what the contract and unit tests check, and what they would miss.
11. Review findings: which are still open in code today?

Write the result to helix-study/02-agents-layer.md
```

## Prompt 04: failure and recovery

Senior panels spend the most time here. The scenarios now match what exists: the agent wrapper, the gateway's dead-letter rules and Cell Router's sweep, plus the designed retry and recall rules.

### 04 — Failure and recovery

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.
Temporal failure concepts and the return-vs-raise trade-off are in
helix-study/00t-temporal-primer.md part 7; refer to them, do not repeat.

Topic: What happens when things fail in Helix - in the code that exists, and in the design.

Read:
- services/libs/helix_platform_libs/src/helix_platform_libs/agent_activity/broker_clients.py
- services/trigger_gateway_svc/src/trigger_gateway_svc/consumer/servicebus_consumer.py,
  services/trigger_gateway_svc/src/trigger_gateway_svc/main.py (receive loop and error backoff),
  services/libs/helix_trigger_lib/src/helix_trigger_lib/normalize.py
- services/cell_router_svc/src/cell_router_svc/consumer/intake.py, and the sweep code
  (search cell_router_svc for "sweep")
- services/trigger_intake_svc/src/trigger_intake_svc/dedup/idempotency_store.py
- vendor-kit/schemas/error-taxonomy.json
- docs/AGENT_INVOCATION_UNIFIED_FLOW.md (Phase 2 retry section only)
- docs/adr/ 0022, 0023, 0029 (Decision only)

For each scenario: what happens step by step, the final state, each step tagged
[CODE] or [DOCS-ONLY].
A. An LLM or Document Intelligence call times out inside an agent.
B. An agent raises an unexpected exception (not BrokerError).
C. An agent returns a failed envelope.
D. The agents worker pod is killed mid-activity. With no heartbeat on single-shot
   agents, when does Temporal notice, and what runs again?
E. Cell Router crashes after writing the workflow_directory row, before the Temporal
   start. What does the sweep do (grace 5 min, interval 10 min, batch 100)?
F. Temporal is down when Cell Router tries to start a workflow.
G. The same upload is sent twice: with and without an Idempotency-Key header,
   and across two Intake replicas (in-memory stores).
H. A poison message (MissingCaseId) reaches the Trigger Gateway: redelivery and dead-letter.
I. A bad agent version is released (ADR 0022 recall and quarantine).
J. A reviewer never acts on a gate (ADR 0023).
K. A broker returns 4xx (permanent) vs 5xx (transient): does broker_clients.py
   tell them apart, or does every error retry?

Then answer:
1. error-taxonomy.json: categories, retryable or not, where code uses it
   ([NOT FOUND] if unused).
2. Designed retry policy vs what code sets today. Where should it be set
   (workflow config, orchestrator, or activity options)?
3. Exactly-once: which side effects could run twice today, and what the
   effect_ledger design would change.
4. Failures not handled today: one line each, ranked by risk.

Write the result to helix-study/04-failure-recovery.md
```

## Prompts 07 and 09: deployment, scale and operations

07 merges the old 07 and 08; 09 merges the old 09 and 14. Both read config files more than code, so Sonnet at medium effort is enough.

### 07 — Deployment and scale

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.

Topic: How Helix is deployed, scaled and load-tested.

Read:
- infra/helm/agents-worker/ (all files), infra/helm/identity-policy/values.yaml,
  infra/helm/_partials/ (all), infra/k8s/, infra/README.md
- agents/Dockerfile, plus the Dockerfiles of trigger_intake_svc, trigger_gateway_svc,
  cell_router_svc and registry_svc
- services/docker-compose.yaml, docker-compose.dev.yaml
- agents/src/agents/perf/ (all), agents/scripts/run_load_test.sh, agents/tests/perf/
- docs/spec/*agent-deployment-option-a*, docs/implementation/platform-at-scale-topology.md
- docs/spec/*azure-technology-stack* (service list only)
- docs/adr/ 0013, 0014, 0016, 0020, 0024 (Decision only)

Answer:
1. Deployable units table: image, base image, port, Helm chart (or none).
2. agents-worker chart walk-through: deployment.yaml (resources, probes, env, secrets,
   service account and workload identity), scaledobject.yaml (scaler type, query,
   thresholds), and how one chart deploys two pools via CORE_AGENTS_QUEUE_CLASS.
3. values-dev, staging, prod and dummy: what differs. Table.
4. How Temporal is hosted: local (compose), dev cluster (temporal-frontend.dev...), and
   the design (one cluster per cell, its database). What is decided vs open.
5. Cells, control plane, data plane and namespace isolation (ADR 0014, 0020, 0024):
   plain explanation with one diagram.
6. "Agent deployment option A": what it is, why temporary, what replaces it.
7. Azure services table: service, purpose, built or designed.
8. Load test: what it sends, what it measures, committed results ([NOT FOUND] if none).
9. The designed bottleneck: LLM rate limits, threads, Temporal or brokers? Use the
   designed SLOs, thread pool sizes and KEDA thresholds in FACTS.md.
10. With no CD workflow, how would a change reach AKS today? [NOT FOUND] if undocumented.

Write the result to helix-study/07-deploy-scale.md
```

### 09 — Operations: observability, audit, CI/CD

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.

Topic: Operating Helix - observability, audit, CI/CD and supply chain.

Read:
- infra/observability/ (all)
- services/audit_svc/src/audit_svc/migrations/versions/ (both files)
- logging, metrics and tracing setup: search services/libs and agents/src for logging,
  structlog, otel, opentelemetry, prometheus, metric, arize; read only the setup functions
- services/cell_router_svc/src/cell_router_svc/main.py (/metrics endpoint only)
- .github/workflows/ (all 7 files), .github/actions/setup-opa/action.yml, .github/CODEOWNERS
- docs/spec/*global-audit-index-observability-design*, *observability-metrics-data-model-design*,
  *arize-agent-observability-design*, *vendor-agent-telemetry-contract-design*,
  *supply-chain-cicd-gate-design*, *sbom-supply-chain* (summary and decisions only)

Answer:
1. Logs: library, format, fields. Is case_id or workflow_id on every line?
2. Metrics: every metric defined in code (name, type, labels, file).
   Are Temporal SDK metrics enabled?
3. Temporal counts a returned failed envelope as a successful activity. Does any
   metric, log or audit entry record the envelope status? [NOT FOUND] if none.
4. Tracing: OpenTelemetry or Temporal interceptors anywhere? [NOT FOUND] if none.
5. The Fluent Bit vendor-agent filter: what it does and why.
6. Audit design: audit_log, outbox, poller, Event Hub, index. What is built?
   Why an outbox? Explain the dual-write problem simply.
7. Arize: what the design sends, how PHI is kept out, built or not.
8. Debug walkthrough: "case X produced a wrong annotation" - what you can use today,
   and what the design adds.
9. Each GitHub workflow in one table: trigger and paths, jobs, what is tested,
   image registry, tag, auth (OIDC or secret).
10. The setup-opa action and the three identity-policy workflows as one policy pipeline.
11. Supply-chain gate and SBOM: designed vs built. What stops a bad change today?
12. Status table: logging, metrics, tracing, dashboards, alerts, LLM observability,
    audit, CI, CD - [CODE] / [DOCS-ONLY] / [NOT FOUND].

Write the result to helix-study/09-operations.md
```

## Prompts 10, 12 and 13: security, catalog and the LLM layer

13 matters most for an AI/ML role, so run it before the other two. 12 merges the old vendor and registry prompts.

### 13 — LLM and model layer

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.

Topic: The LLM and model layer - which agents use models, how they call them,
how quality is measured.

Read:
- agents/src/agents/registry.py (to find the 2 activities on core-agents-llm)
- for those 2 agents, and for logo_agent (the planned first reasoning-loop agent):
  the core/ files that build prompts or call models
- any agent that reads AZURE_* or Document Intelligence settings
  (search agents/src for AZURE_, openai, DocumentIntelligence)
- broker_clients.py (llm_broker_call only)
- docs/agents/UAIS_AGENT_MODEL_PORTING_GUIDE.md, docs/agents/2026-10-16-uais-connector-*
- agents/notebooks/uais_model_connectivity_report.ipynb (markdown cells and result summary only)
- docs/spec/*annotated-pdf-metrics-backend-design*,
  docs/implementation/12-agent-metrics-hitl-gating-guideline.md
- docs/adr/0007-*.md (full)

Answer:
1. Which agents call an LLM or an Azure AI service, through what client, with what config?
2. Table: agent, model or service, temperature, max tokens, structured output, retries.
3. Where prompts live and how they are versioned (Registry prompt_versions?).
   One real prompt, explained.
4. Output parsing and validation; what happens on malformed output.
5. UAIS: what it is, how agents reach models through it, what porting required,
   what the connectivity report found.
6. ADR 0007: why regulated translation stays human (MCS) - the risk reasoning.
7. Quality: metrics, thresholds that raise gates, the annotated-PDF metrics backend,
   golden data. Real numbers only.
8. Guards against hallucination before a human sees the output.
9. Where the LLM broker fits, and what happens to direct AZURE_* access once it exists.
10. Why the LLM pool gets 64 threads and a lower KEDA threshold than the
    deterministic pool: what the numbers say about LLM call latency.

Write the result to helix-study/13-llm-layer.md
```

### 10 — Security and the trust boundary

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.

Topic: Security in Helix - identity policy, brokers, capability tokens, PHI handling.

Read:
- services/identity_policy/ (code, .rego files, Rego tests), infra/helm/identity-policy/values.yaml
- services/trust_boundary/memory_broker/ (api/app.py, token check, quota, migrations)
- services/trust_boundary/phi_broker/ migrations (both)
- services/libs/helix_platform_libs/src/helix_platform_libs/content_reference.py
- broker_clients.py (token code, L22-L69)
- services/trigger_intake_svc/src/trigger_intake_svc/config.py and api/status.py (auth only)
- docs/spec/*identity-policy-design*, *trust-boundary-sandbox-brokers-design*,
  *memory-broker-design* (decisions and flows only)
- docs/adr/ 0015, 0018, 0019, 0021, 0024, 0026, 0030, 0033 (Decision only)
- docs/implementation/pending-decisions.md (rows 10-14)

Answer:
1. Identity and Policy Bundle Service: push and pull flow, signing and verification,
   where OPA runs, one real Rego rule explained line by line.
2. All five brokers: what each brokers, and whether it is built, schema only or empty.
3. No ambient authority (ADR 0015) in simple words, with one attack it stops.
4. Capability tokens: who mints them, claims inside, lifetime, header transport
   (ADR 0026), and what the memory broker checks today.
5. Content References are unsigned today: what attack does that allow, and what
   would signing fix?
6. Crypto-shredding, retention and legal hold (ADR 0021) in plain words, and the
   phi_broker tables that support them.
7. Row-level security: which tables use it, and how app.tenant_id is set.
8. Intake auth off by default, unauthenticated status endpoint, DNS-rebinding gap
   in pull mode: each risk in simple words.
9. Security controls designed but not built: list.

Write the result to helix-study/10-security.md
```

### 12 — Registry, version pinning and the vendor kit

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.

Topic: The platform catalog - Registry, version pinning, and the vendor kit.

Read:
- services/registry_svc/src/registry_svc/ (routers, store, events) and its migrations
- vendor-kit/ (schemas, src/helix_vendor_kit/conformance, harness, reference_agent -
  entry files only)
- docs/vendor-integration/vendor-development-kit-technical-guide.md (sections 1-4)
- docs/adr/ 0002, 0005, 0008, 0010, 0018, 0022, 0025, 0027 (Decision only)

Answer:
1. Registry endpoints table: method, path, purpose. Catalog tables and key columns.
2. resolve-pins: input, output, rules. How a case gets fixed versions of agents,
   prompts, rules and connectors.
3. Explicit repinning, no auto-adopt (ADR 0008): why safety over freshness.
4. Recall and quarantine (ADR 0022): what Registry supports today.
5. Registry events on Service Bus (registry-events): which events, and who consumes them.
6. Shared rule library vs a BRMS (ADR 0005); shared library references (ADR 0010).
7. Vendor kit: the four schemas, SDK, conformance tests, harness and reference agent -
   what each does.
8. Vendor onboarding from code to production, every gate (ADR 0025, 0027).
9. Internal agent vs vendor agent: invocation differences, as a table.

Write the result to helix-study/12-catalog-vendors.md
```

## Prompts 15–16: trade-offs and the cheat sheet

15 reads only the decision parts of the ADRs and reuses 00's comparison table. 16 runs last and reads only four sections of each earlier file.

### 15 — Design decisions and trade-offs

```text
Follow #file:helix-study/STYLE.md (sections 4-7 can be short).
Known facts: #file:helix-study/FACTS.md.

Topic: Design decisions and trade-offs - all ADRs, the review, open decisions.

Read:
- docs/adr/ all 33 files: Decision, Alternatives and Consequences sections only
- docs/reviews/2026-10-06-core-agents-temporal-framework-review.md (findings and verdict)
- docs/implementation/pending-decisions.md
- docs/future_spec/ (file names and first paragraph only)
Reuse helix-study/00-big-picture.md section 11 (Q7 table) and
helix-study/00t-temporal-primer.md part 10 (ADR 0011, 0019) instead of re-reading them.

Answer:
1. Table of all 33 ADRs: number, decision in one plain line, problem solved,
   alternative rejected, cost, and built / partly / not built (use FACTS.md).
2. The 8 ADRs a CTO is most likely to challenge: decision, strongest argument against,
   the ADR's answer, my one-line verdict.
3. A Mermaid diagram of the main ADR dependency chains.
4. ADR 0009: what the mock POC proves and does not prove.
5. Review findings: what changed after the review, what is still open.
6. Pending decisions and future specs: why each matters.
7. The 5 decisions hardest to reverse, and why.

Write the result to helix-study/15-tradeoffs.md
```

### 16 — Interview cheat sheet (run last)

```text
Follow the Language and Truth rules in #file:helix-study/STYLE.md.
Known facts: #file:helix-study/FACTS.md.
Read sections 1, 4, 9 and 10 of every numbered file in helix-study/, and only the
interview questions of 00t-temporal-primer.md. Nothing else.

Write:
1. 30-second pitch: what Helix is, why it is built this way, and its honest status
   (a design-led platform, partly built).
2. A 2-minute walkthrough I can say out loud, following one case end to end and
   saying clearly which parts are built and which are designed.
3. One Mermaid diagram of the whole system, max 15 boxes, built vs designed marked.
4. The 30 hardest interview questions across all files: 3-5 sentence answers,
   one file reference each.
5. Numbers I can quote: real values only, with source.
6. Do-not-claim list: everything [DOCS-ONLY] or [NOT FOUND].
7. Ten trade-off one-liners: "We chose X over Y because Z; the cost is W."
8. Gaps I can discuss honestly, and how I would close the top 3.

Write the result to helix-study/16-cheat-sheet.md
```

## Utility prompts: single file, fact-check, follow-up

Use these alongside the topic prompts. The file deep-dive replaces "give me a 15,000 ft view of this file". Run the fact-check only on files whose numbers you will quote: it re-reads every cited file, so it is not cheap.

### File deep-dive (any one file)

```text
Follow the Language and Truth rules in #file:helix-study/STYLE.md.

Explain #file:<path/to/file.py> to me, one level at a time.

1. One-line answer: what this file is for.
2. Where it sits: who calls it (search the repo), what it calls, and what
   happens before and after it in one case's journey.
3. 30,000 ft: the idea in 3-5 sentences. No technical terms, no numbers.
4. Why it exists: what would break if this file were deleted?
5. 10,000 ft: each class and function as What / Why / How, 2-3 lines each,
   in the order they run (not file order).
6. 1,000 ft: trace one real input through the file, step by step,
   with real field names and values.
7. Tricky lines: the 5 lines most likely to confuse a reader, explained.
8. Failure: what errors it raises or catches, and what the caller does with them.
9. Tests: which tests cover this file, and what they do not cover.
10. Two interview questions about this file, with answers.

Write the result to helix-study/files/<file-name>.md
```

### Fact-check pass (run after every topic file)

```text
Fact-check #file:helix-study/<NN-topic>.md against the repo.

- For every claim tagged [CODE]: open the cited file and lines. Confirm the claim
  matches the code exactly. If wrong, fix the text. If the code does not exist,
  change the tag to [DOCS-ONLY] or [NOT FOUND].
- For every row in "Exact settings": confirm the value in the cited file.
- For every [NOT FOUND]: search once more with different keywords before keeping it.

At the top of the file, add a section "Fact-check results" listing every change.
Change only this one file.
```

### Follow-up when one part is unclear

```text
In #file:helix-study/<NN-topic>.md, section "<heading>", I do not understand:
"<paste the sentence>".

Explain only this piece. Start from the simplest version, then add one detail
at a time. Use one small example. Then rewrite that paragraph in the file in
simpler words.
```
