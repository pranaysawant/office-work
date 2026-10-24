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
| 01 | 01-orchestration.md | Orchestrator and human gates: design vs built | Opus, high | Done |
| 02 | 02-agents-layer.md | Inside an agent, registration, handoff, gate signals | Opus, medium | Done |
| 04 | 04-failure-recovery.md | How agents survive real failures: verdicts, gaps, fixes | Opus, high | Done |
| 13 | 13-llm-layer.md | Prompts, models, credentials, evaluation, cost | Opus, medium | Must, next |
| 07 | 07-deploy-scale.md | Helm, KEDA, capacity vs provider quota, cells, Azure | Sonnet, medium | Must |
| 15 | 15-tradeoffs.md | All 33 ADRs, the review, open decisions | Sonnet, high | Must |
| 09 | 09-operations.md | Designed observability, audit, alerts, CI/CD | Sonnet, medium | Should |
| 10 | 10-security.md | Policy service, brokers, tokens, PHI, secrets | Sonnet, medium | Should |
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
# Helix facts - verified in the 00, 00t, 01, 02 and 04 study files
Treat these as known. Do not re-read files just to re-confirm them.
Read a listed file only when a question needs a detail that is not here.
Temporal concepts: helix-study/00t-temporal-primer.md. Orchestrator and gate design:
helix-study/01-orchestration.md. Agents, gate rules, thresholds: helix-study/02-agents-layer.md.
Failure scenarios, retry budget, scorecard: helix-study/04-failure-recovery.md.

## Build status
Built:        trigger_intake_svc, trigger_gateway_svc, cell_router_svc (bugs), registry_svc,
              identity_policy, trust_boundary/memory_broker, libs/*, agents/ worker
Stubs inside: intake AV scan, in-memory blob store, PHI key, dedup, case-id counter,
              capability-token minting, write_non_phi_blob (returns its input)
Schema only:  orchestrator_svc (cases, effect_ledger), gate_svc (gates, decisions),
              audit_svc (audit_log, outbox), trust_boundary/phi_broker
Empty:        review_console_svc, connector_broker, llm_broker, agent_sandbox_adapter,
              services/tests/e2e
NOT FOUND:    production @workflow.defn (GenericOrchestratorWorkflow has no worker),
              code reading MCS_workflow_config_v1.json, .proto / gRPC, outbox poller,
              Lane A consumer, Registry /triggers route, Cell Router /start route,
              workflow patching, continue-as-new, Gate Service API, sweeper,
              runtime telemetry (Prometheus / OTel) in agents and the wrapper,
              alert rules anywhere, a RetryPolicy passed anywhere

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
         wrapper.py:L1-L136; envelope.py:L24-L113; contract.py; artifacts.py; broker_clients.py
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
Heartbeat: only reasoning_loop / harness_loop agents get report_progress -> heartbeat
  (wrapper.py:L55-L81); single-shot agents use a no-op. logo drops it on its core path.
Worker: TEMPORAL_NAMESPACE default "default" (worker.py:L21); CORE_AGENTS_QUEUE_CLASS
  all | deterministic | llm picks the queues (L33-L40); one Worker per queue via
  asyncio.gather (L83-L86); production = one Deployment per class, "all" is for dev (L1-L6).
  registry.py "dummy" profile registers only the two dummy agents (L15-L22).
Test chain: DummyChainProbeWorkflow, id probe-dummy-chain-wf, queue core-agents-deterministic,
  start_to_close 30 s per activity (_dummy_chain_probe_workflow.py:L16, L27) - the only
  timeout passed in code; WorkflowEnvironment.start_local() (test_dummy_agents_worker_e2e.py:L18).
Cell Router start method (temporal_client.py:L106-L200): named start_workflow but calls
  execute_workflow (blocks up to the 30-day run timeout); TypeError from workflow= plus a
  positional input; wrong keyword workflow_id_reuse_policy (Python SDK: id_reuse_policy);
  comment L185-L186 wrongly says it returns a handle, so run_id at L187 would be empty.
  Correct parts: REJECT_DUPLICATE default (L112, L163-L164), deterministic ID (L125-L130),
  WorkflowAlreadyStartedError treated as success (L116-L120, L195-L197).
Signal: Gateway raises NoLiveRun when the Directory row is missing or status != "open"
  (signal_dispatch.py:L43-L49) -> dead-letter rejected_no_run; else it signals the run_id
  stored in the row (L51-L57). Directory status: open | dehydrated | closed
  (cell_router_svc workflow_directory.py:L36).

## Orchestrator and gates design (01)
Design: GenericOrchestratorWorkflow walks a recipe tree (execute_node): step, sequential,
  parallel (join all only), loop_until (on_exhausted gate | fail), subflow (inline,
  depth <= 5). No if/else node. Spec: docs/spec/2026-09-16-generic-orchestrator-workflow-
  design.md; sketch: docs/implementation/04-generic-orchestrator-implementation.md L131-L232.
Designed activities: PinVersions, LoadWorkflowConfig, BuildContext, CheckEffectLedger,
  RecordEffect, WriteAudit, WriteSla, WriteOutcome, RaiseGate, Dehydrate. None built.
Registry POST /resolve-pins is built: flat list pins[{entity_type, entity_id, version}]
  (registry_svc resolve_pins.py:L24-L58); the 04 sketch expects a dict.
Config: MCS_workflow_config_v1.json fails workflow-config.schema.json (missing tenant_id,
  recipe); no additionalProperties:false; no field for task queue, timeouts or retry.
  MCS min/max/escalation_sla_hours and auto_approve_gate are defined nowhere.
cases: 7 statuses; trigger case_transition_guard BEFORE UPDATE OF status:
  created->in_progress; in_progress->awaiting_review|completed|rejected|failed|cancelled;
  awaiting_review->in_progress|failed|cancelled; terminal states frozen; a same-state
  update raises; INSERT unguarded. Columns include pinned_versions, dehydrated (bool),
  dehydration_state, SLA clocks; RLS on tenant_id; no column for step outputs.
effect_ledger: PK (workflow_id, step_id, loop_iteration, logical_effect_id), outcome JSONB,
  effected_at; no "started" marker. No MCS step is side_effecting.
gates: gate_type confidence | policy | exception (HITL spec lists 5); status
  open | resolved | escalated | terminal; terminal_disposition failed | park; resolution_type
  approve | override | correction | reject | escalate | timeout; index WHERE status='open'.
  decisions: PK gate_id, no PHI.
Gate design: dehydrate when expected dwell > ~1 h (provisional, arch 6.8); saved state
  {pinned_versions, last_context_snapshot_ref, resume_at_step_id}; sweeper CronJob ~60 s;
  gate token EdDSA JWT, 2 h in-run / 24 h dehydrated; single-winner
  UPDATE ... WHERE status='open'; reviewer holds required_role and is not the submitter.
Spec says agent status ok | needs_gate | failed; code says success | needs_gate | failed.

## Agents layer (02)
Agent folder: activity.py (entry), core/ (legacy code, unchanged), mappers.py (contract <-> core),
  contract/<agent>.contract.json (the real schema authority, loaded at import by contract.py),
  data_model/ and io_models/base.py (reference models, unused at runtime), payload_template.json
  (nested; activities need a flat dict; only the demo notebook flattens it).
Wrapper modes: automatic (core_fn + input_mapper + output_normalizer, wrapper.py:L104-L134);
  custom (decorated function is the whole body; segmentation uses it for its global pipeline_lock).
Input check: presence only on input.payload and step_config, no types, case_id unchecked
  (contract.py:L73-L93). Output check: dynamic pydantic model, extra=forbid (contract.py:L212-L260);
  a failure returns CONTRACT_OUTPUT_VALIDATION_ERROR after the work ran.
Gate status: needs_gate if ANY signal, severity ignored; hitl_required set but unread
  (envelope.py:L86-L91). Code emits 24 rule ids (DETECT_LANG_*, SEG_*, LOGO_*, NTDC_*, BISU_*,
  TR_SUB_AGENT_FAILED); 15 other ids exist only in contracts. Thresholds hard-coded per mapper,
  overridable by step_config.metric_thresholds. Only detect-lang reads contract gate_conditions.
  Full table: 02 section 8a.
Agents: deterministic queue - dummy1, dummy2, detect-lang, segmentation (calls GPT-4.1 and Gemini
  anyway), validation, ntdc, bisu, annotate; llm queue - logo, translation-review.
  validation runs logo, ntdc and bisu in-process in a ThreadPoolExecutor
  (agents/src/agents/activities/validation_agent/activity.py:L101-L107) and collects their signals;
  annotate reads them from final_agent_output.json and emits no signals itself.
  translation-review runs segmentation, the validation children and annotate in ONE activity.
  NTDC = Numbers, Dates, Times, Currencies; BISU (not expanded in code) = bold, italic,
  underline, font size.
LLMs (called directly, not through brokers): segmentation GPT-4.1 mapping + GPT-4.1 judge +
  Gemini embeddings + Azure DI; logo gpt-4o (fallback gpt-4.1, o4-mini, 240 s call timeout);
  ntdc GPT-4.1 optional (use_llm default true); bisu Gemini on Vertex AI (thresholds.json
  llm_review.enabled true; step_config.use_llm ignored). Segmentation core: LLM_TIMEOUT 120,
  LLM_MAPPING_MAX_CONCURRENCY 6, MAX_PAGES 20. core/config.json holds developer paths and a key-file path.
logo: contract says harness_loop, max_iterations 3, exit at 0.85; core is one linear pass
  with a model fallback list.
Handoff: local file paths. Artifacts in /tmp/helix-artifacts/<case>/downstream_artifacts/<agent>
  (artifacts.py:L81-L83); segmentation uses SEGMENTATION_ARTIFACTS_ROOT. No shared volume in
  the Helm chart. Segmentation returns mapped_regions and the run_summary mapping list by value,
  so they enter Temporal history.
Contract activity_options are data only (nothing reads them): 30 s for deterministic agents,
  120 s for logo and translation-review, max attempts 3, logo heartbeat 30 s.
Versions: contract_version 1.0.0 everywhere, never compared; activity name = bare agent_id,
  so two versions of one agent cannot run side by side.
Quality metrics are self-referential: align_f1 treats every mapping as correct; ntdc and logo
  use proxies; segmentation ece fixed at 0.0. Metric code:
  services/libs/helix_platform_libs/src/helix_platform_libs/evaluation_framework/metrics.py.
linguistic-agent-contract.json: draft for an 11th agent (linguist-agent), loaded by nothing.

## Failure behaviour (04)
Retries: no RetryPolicy is passed anywhere, so Temporal's default applies once an orchestrator
  exists: unlimited attempts, 1 s doubling to 100 s, bounded only by the 30-day workflow
  timeout. Raised bad input (ntdc LanguagePairError, annotate FileNotFoundError) would loop.
Worker: no max_concurrent_activities (SDK default 100 slots) against 32 / 64 threads; no
  heartbeat on single-shot agents; Helm sets no terminationGracePeriodSeconds; image tag
  latest, not overridden in prod; memory limit 2 Gi; prod min 4, max 120 replicas.
LLM errors are swallowed: segmentation saves *_mapping_error per region and continues
  (pipeline.py:L3316-L3322); no Retry-After, no max_tokens, no finish_reason check;
  logo returns empty block_analysis on parse error (logo_agent.py:L388-L396, L1076);
  ntdc call_llm returns None and its checks fail open (ntdc llm.py:L82-L103, L168, L206),
  one hard-coded dev URL, 20 s timeout. OpenAI SDK default max_retries 2. No circuit breaker.
Page limit: MAX_PAGES 20 stops silently at page 21 (pipeline.py:L684-L685); Azure DI analyses
  and bills every page ($10 per 1,000 pages, L609); DI poll 300 s; DI cache written only on success.
validation: a raised child exception discards sibling results and retries all three.
broker_clients: every HTTP error -> BrokerError (raised, retried), 4xx and 429 included;
  attempt=1 hard-coded; Retry-After lost; missing token signer is retried too.
error-taxonomy.json: 6 codes (validation_error, unsupported_contract_version, payload_too_large,
  timeout, capability_denied, internal_error); no retryable field in the JSON; used only
  inside vendor-kit.
Cell Router: after a crash, redelivery hits DuplicateCaseError and the start is never retried;
  reconciliation sweep (consumer/reconciliation_sweep.py) ignores run_id='', scans up to 1,000
  open rows, writes terminal_unknown which the table CHECK rejects, has no replica lock;
  mark_orphaned_as_failed has no caller. 11 Prometheus metrics defined, none recorded.
Gateway: MissingCaseId escapes consume_one and stalls its session until MaxDeliveryCount
  (not set in repo); transient dispatch errors are dead-lettered at once; no DLQ re-drive.
Intake: dedup dict and case_id counter in process memory; no message_id on publish; no try
  around publish; no content-hash dedup; no page-count check.
Detection: no alert rules; Gateway logs via logging.basicConfig; agent cores print.
Registry quarantine status is built (registry_svc domain/lifecycle.py:L10-L14); the
  quarantined_version_pin gate is not.

## Key values
case_id case_<YYYY>_<MM>_<DD>_<NNNNN>; workflow_id {tenant_id}:{workflow_type}:{case_id}
Reuse policy REJECT_DUPLICATE; workflow execution and run timeout 30 d; task timeout 10 min
Queues: core-agents-deterministic (8 activities, 32 threads, prod 64), core-agents-llm (2, 64 threads)
Worker graceful shutdown 30 s
KEDA: metric temporal_activity_task_queue_backlog; deterministic min 1 max 40 threshold 10;
      llm min 1 max 60 threshold 5; polling 30 s; cooldown 300 s
Designed retry (docs only, docs/AGENT_INVOCATION_UNIFIED_FLOW.md Phase 2): initial 1000 ms,
      backoff 2.0, max attempts 3, start-to-close 60000 ms, heartbeat 30000 ms
MCS SLA: end_to_end 1440 min, per_step 480 min. Max upload 25 MiB.
Designed scale: 1B+ runs/year, ~32 starts/s average; p95 < 2 s deterministic step,
      < 8 s AI step. Orchestrator pool: D4s_v5, 1-5 nodes, 3 workers (04 doc).
Broker HTTP timeout 20 s; broker URLs default to localhost:8081 / 8082.

## Design decisions already summarised
00t part 10: spec 2.2 (Little's Law, Cassandra, dehydrate), ADR 0011, ADR 0019.
01 sections 7.9 and 9: ADR 0004, 0006, 0012, 0020, 0023.
02 sections 3 and 9: ADR 0011 in practice (logo loop), ADR 0019 gaps (paths, values in history).
04 P and B1: ADR 0022 (recall half built), ADR 0029, the error taxonomy.

## Agent result envelope
{status: success | needs_gate | failed, result, produces_artifacts, gate_signals,
 confidence, errors, sla, audit_entry}
Business failures are RETURNED as failed envelopes (Temporal sees success, no retry).
Broker errors are RAISED (Temporal retries).

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

**01-orchestration.md**

- Several long lines end mid-sentence (sections 5 and 7.1–7.7). If they are cut in the file too, not only in your copy, ask Copilot in the same chat: "In 01-orchestration.md, complete the lines that end mid-sentence in sections 5 and 7." That is a cheap request.
- Section 8 says history shards are "fixed at namespace creation". In Temporal the shard count is fixed when the cluster is created and covers every namespace in it. Say "cluster" in interviews.
- Section 7.1 calls an `EscalateGate` activity. That name is Copilot's; the docs' activity list does not include it.
- One gap the file missed: the trigger rejects a same-state update, and activities retry. If `WriteOutcome` commits and its worker dies before reporting back, the retry writes the same status again and fails. Good to raise in an interview; the fix is in the TransQA Mini lessons.

**02-agents-layer.md**

- Sections 7b–7d are scrambled: duplicated headings and code lines mixed into prose. A few table headers are broken (section 5 metrics table, the confidence table in 7b, the segmentation config row in 8d). Ask Copilot in the same chat: "In 02-agents-layer.md, rewrite sections 7b, 7c and 7d cleanly and fix the broken table headers in sections 5, 7b and 8d. Change nothing else."
- The numbers in section 5 (42 blocks, 37 mappings, 84 s duration, timestamps) are an example Copilot made up to show the math. The formulas are real; the values are not measured. Never quote them as results.
- Missed point 1, hidden queueing: segmentation holds a global lock, and its pool has 32 threads. Once a worker accepts a task it leaves the queue backlog, so tasks waiting for the lock inside a pod are invisible to KEDA, and their start-to-close clocks are already running. With the contract's 30 s timeout, the waiting ones would time out and retry, paying for LLM calls again.
- Missed point 2, gate in the wrong place: the MCS config puts the human gate on annotate, but annotate never returns needs\_gate; segmentation and validation do. Under the designed "needs\_gate raises a gate" rule, the case would pause at steps that have no gate policy, and the design does not say what happens then.
- Missed point 3, pins that cannot be honoured: PinVersions pins agent versions, but each activity is registered under its bare agent\_id, so a worker runs only one version. A case pinned to an older version cannot get it without versioned activity names or Temporal Worker Versioning.
- Missed point 4, history size and privacy: segmentation returns its mapping list by value. If that list carries text spans, document text lands in Temporal history (against ADR 0019), and a long document can pass Temporal's payload limit (about 2 MB by default).

**04-failure-recovery.md — corrections**

- "With no timeout set, Temporal never learns" (scenario A and the P-default row) is wrong. The SDK refuses to schedule an activity without a start-to-close or schedule-to-close timeout, so some timeout always exists. The real risk is a timeout far longer than the work, with retries bounded only by the 30-day workflow timeout.
- Scenario C's "9,600 starts in the Temporal backlog after recovery" mixes two queues. During the outage, starts fail at Cell Router and go back to Service Bus (or hit the DuplicateCaseError bug); they never queue inside Temporal. The herd after recovery comes from Service Bus redelivery plus Temporal's own retries.
- Scenario B understates the queueing. The worker has 100 activity slots (SDK default) but only 32 threads, so even without the lock, up to 68 accepted tasks wait for a thread with their timers running.
- Scenario K's fix, "pin the snapshot with no auto-upgrade", has a cost: when Azure retires that version, a pinned deployment stops serving. Pinning means owning a migration calendar.
- Every verdict assumes an orchestrator exists and passes no retry policy. In an interview, say "as the code would behave once an orchestrator calls it".

**04 — gaps it missed** (my review; strong interview material)

1. **Scaling cannot buy provider capacity.** KEDA scales the LLM pool on backlog, but the real limit is the Azure OpenAI quota. More pods during a 429 storm make it worse. LLM concurrency (replicas × slots) should be capped at the quota.
2. **No admission control.** Intake keeps accepting cases during an outage. Nothing returns 429 or 503 to callers, so the backlog and the bill grow with work the system cannot finish.
3. **Gates become the failure sink.** Many fixes route problems to human gates. Without a gate-rate metric and an alert per rule, an outage turns into a review queue nobody can clear.
4. **No way to fix cases that already went out wrong.** After the ntdc fail-open bug is fixed, which completed cases were affected? Without model, prompt and code versions recorded per case, you cannot find and reprocess them.
5. **No cost cap.** 04 computes the retry budget, but nothing stops spend per case or per tenant.
6. **Local disk growth.** No cleanup of `/tmp/helix-artifacts` appears in what 04 read, so a busy pod can fill its disk and be evicted.
7. **No checkpoints inside a step.** Segmentation's per-region results could be saved (heartbeat details or Blob), so a retry resumes at region N instead of starting over.
8. **No fault-injection tests.** None of the 17 scenarios is tested, and no game day is described.

**How to answer "How does your system survive failures?" in 60 seconds**

"Helix's design has the right building blocks: durable workflows, deterministic IDs and a quarantine model. The code that exists shows three failure patterns. Retries are unbounded, because no retry policy is set. Failures degrade silently, because LLM errors are swallowed and ntdc fails open. And handoff breaks across pods, because steps pass local file paths. My first three fixes would be: one shared activity-options helper with bounded retries, heartbeats and non-retryable input errors; typed LLM errors that turn into gate signals instead of empty results; and artifacts passed as Blob references. Then four alerts: retries rising, cases past their SLA, gate rate per rule, and dead-letter count."

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
what gate signals they raise, and how data passes between them.

Read:
- agents/src/agents/activities/segmentation_agent/ (all files) - the worked example
- agents/src/agents/activities/logo_agent/activity.py and core/ (the planned first loop agent)
- mappers.py of validation_agent, ntdc_agent and annotation_agent (gate signals, thresholds)
- every other agent: activity.py and contract/ only
- agents/src/agents/io_models/base.py, agents/linguistic-agent-contract.json
- agents/src/agents/legacy_compat/ (first 60 lines of each file)
- services/libs/helix_platform_libs/src/helix_platform_libs/agent_activity/ (all files;
  skip the wrapper.py parts already summarised in FACTS.md)
- agents/tests/contract/ (file names, plus one test in full); agents/tests/unit/ (file names only)
- docs/agents/AGENT_LAYER.md
- docs/reviews/2026-10-06-core-agents-temporal-framework-review.md (findings list)
Skip orchestrator and gate design (covered in 01).

Answer:
1. Each part of segmentation_agent (activity.py, core/, data_model/, mappers.py,
   contract/, payload_template.json), and why an agent is split this way.
2. Trace segmentation_agent's payload_template.json from input to output envelope,
   with real field names and one realistic value per field.
3. The wrapper beyond FACTS.md: input model validation, how sla, confidence and
   audit_entry are filled, metrics, the rounding helpers, and the reasoning_loop mode.
4. Table of all 10 agents: queue (deterministic or llm), purpose in one line, input,
   output, LLM used (yes/no), external service called, in the MCS config (yes/no),
   single-shot or reasoning loop, gate rules it can emit.
   Explain names like bisu and ntdc only if the code does.
5. Gate signals: every rule_id the agents can emit, its severity, the threshold that
   triggers it, and the file and line. How do validation sub-agents' signals reach annotate?
6. logo_agent: is it ported? What would its loop look like (max_iterations, tools)?
7. linguistic-agent-contract.json and io_models/base.py field by field, including
   CaseContext and GateSignal. Who must follow them?
8. Handoff today: agents pass file paths, and annotate reads paths from disk. What breaks
   when consecutive steps run in pods on different nodes? How would references fix it?
9. Contract versioning and validation: where checked, what happens on a mismatch.
10. Artifacts: produces_artifacts and the write_non_phi_blob passthrough - where do
    files really go today?
11. Tests: what the contract and unit tests check, and what they would miss.
12. Review findings: which are still open in code today?

Write the result to helix-study/02-agents-layer.md
```

## Prompt 04: failure and recovery

Senior panels spend the most time here. The scenarios now match what exists: the agent wrapper, the gateway's dead-letter rules and Cell Router's sweep, plus the designed retry and recall rules.

### 04 — Failure and recovery

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.
Refer to, do not repeat: 00t part 7 (Temporal failure concepts, return vs raise),
01 section 9 (orchestrator-design failures), 02 sections 7a and 9 (agent-level errors).

Changes for this file:
- Act as a principal engineer reviewing Helix before a production launch. First describe
  what the code does, tagged; then judge it plainly.
- [IDEA] is allowed in every scenario, not only in a weak-points section. Each idea must
  name a concrete mechanism (a setting, a pattern, a table, a Temporal feature), not a slogan.
- Use this shape instead of STYLE's 12 sections: 1 one-line answer; 2 altitude 30,000 ft;
  Part A; Part B; Interview Q&A; Glossary; Files read.
- When no retry policy is passed, Temporal's default applies (unlimited attempts, backoff
  1 s doubling to 100 s). Say for each scenario which policy applies today.

Topic: How Helix agents survive real-world failures - what exists, what breaks,
and what a production-grade design would do instead.

Read:
- services/libs/helix_platform_libs/src/helix_platform_libs/agent_activity/broker_clients.py
- services/trigger_gateway_svc/src/trigger_gateway_svc/consumer/servicebus_consumer.py,
  services/trigger_gateway_svc/src/trigger_gateway_svc/main.py (receive loop and error backoff),
  services/libs/helix_trigger_lib/src/helix_trigger_lib/normalize.py
- services/cell_router_svc/src/cell_router_svc/consumer/intake.py, and the sweep code
  (search cell_router_svc for "sweep")
- services/trigger_intake_svc/src/trigger_intake_svc/dedup/idempotency_store.py
- vendor-kit/schemas/error-taxonomy.json
- agents/src/agents/activities/segmentation_agent/core/src/pipeline.py: only pipeline_lock,
  where LLM_TIMEOUT and MAX_PAGES are applied, and any retry loop around LLM calls
- agents/src/agents/activities/logo_agent/core/logo_agent.py L400-L430 (model fallback)
- agents/src/agents/activities/ntdc_agent/core/NTDC_Agent/llm.py (retry and error handling only)
- agents/src/agents/activities/validation_agent/activity.py L95-L140 (child failures, thread pool)
- docs/AGENT_INVOCATION_UNIFIED_FLOW.md (Phase 2 retry section only)
- docs/adr/ 0022 and 0029 (Decision only)

Part A - scenarios. For each one write exactly these five labelled lines:
  What happens: the steps, each tagged [CODE] or [DOCS-ONLY]
  Verdict: SURVIVES / DEGRADES / BREAKS, and the final state of the case
  Blast radius: one case, one pod, one queue, one tenant, or everyone
  Better design [IDEA]: the concrete fix
  Interview answer: 2-3 sentences I can say out loud

Infrastructure and platform
A. The agents worker pod is killed mid-activity (no heartbeat on single-shot agents).
B. 10 segmentation tasks reach one pod with a 32-thread pool and pipeline_lock.
   Are the waiting tasks visible to the KEDA backlog metric? Do their timeouts tick?
C. Temporal is down for 5 minutes, then recovers: backlog, retries and KEDA afterwards.
D. Cell Router crashes after writing the workflow_directory row, before the Temporal start
   (sweep: grace 5 min, interval 10 min, batch 100).
E. The same upload twice: with and without Idempotency-Key, across two Intake replicas.
F. A poison message (MissingCaseId) reaches the Trigger Gateway.

LLM and external services
G. One LLM call hangs (LLM_TIMEOUT 120 s) while the contract activity timeout is 30 s.
H. Azure OpenAI returns 429 rate limits for 10 minutes at peak load.
I. One model provider is down for an hour (fallbacks exist only in logo's model list).
J. The LLM returns malformed JSON, a refusal, or a truncated answer (max tokens hit).
K. The model behind an endpoint changes silently and quality drops.
L. A 300-page PDF arrives (MAX_PAGES 20): memory, time and cost.

Agents and data
M. ntdc raises LanguagePairError, or annotate raises FileNotFoundError (bad input, raised).
N. One validation child (logo) fails while ntdc and bisu succeed.
O. A step's output file is missing on the next pod (local-path handoff).
P. A bad agent version is released (ADR 0022 recall and quarantine).
Q. A broker returns 4xx vs 5xx: does broker_clients.py tell them apart?

Part B - cross-cutting
1. error-taxonomy.json: categories, retryable or not, where code uses it ([NOT FOUND] if unused).
2. Retry budget: the worst-case number of LLM calls for one document if every layer retries
   (activity attempts x retries inside core x model fallbacks). Use real numbers from code,
   contracts and Temporal defaults, and show the multiplication.
3. Exactly-once today: which side effects could run twice (LLM calls, files, blob writes,
   Service Bus messages, audit rows)?
4. Detection: for each scenario, how an operator finds out today
   (metric, log, alert, Temporal UI, or nothing).
5. Resilience scorecard, one row per failure class (worker crash, timeout, rate limit,
   provider outage, bad output, bad input, duplicate, poison message, bad release,
   data loss); columns Detect / Contain / Recover / Prevent; each cell built, designed
   or missing.
6. The top 5 fixes ranked by risk removed per unit of effort, each naming the scenarios it fixes.

Interview Q&A: the 5 hardest failure questions a CTO would ask about Helix, each answered
in 4-6 sentences: what exists, what is missing, and what I would do.

Write the result to helix-study/04-failure-recovery.md
```

#### Before you read 04: a frame for failure questions

Interviewers judge failure answers by their structure, not by how many tools you name. Answer every "what if X fails" question in this order:

1. **Classify it.** Transient (a retry helps), permanent (a retry never helps), unknown outcome (did the side effect happen?), overload (too much work), or bad release (our own change).
2. **Detect it.** Name the exact signal: a metric, an alert, a Temporal event, a gate count. "We would notice" is not an answer.
3. **Contain it.** Limit the blast radius: timeouts at every layer, separate worker pools, concurrency limits, rate limiters, circuit breakers.
4. **Recover by class.** Retry with backoff and jitter (transient); fail fast to a human (permanent); reconcile from a record (unknown outcome); queue and shed load (overload); roll back or quarantine (bad release).
5. **Prevent it.** Tests, canary releases, evaluation gates, budgets.
6. **Measure it.** End with the number you would watch to prove the fix works.

**Survival kit for LLM agents in production.** Use these as your "better design" answers.

| Risk | Mechanism |
| --- | --- |
| Rate limits (429) | Concurrency per provider sized to quota; a token-bucket limiter; honour Retry-After; backoff with jitter |
| Provider outage | Circuit breaker per provider; fallback model chain; queue and resume instead of failing cases |
| Slow or hung call | Layered timeouts: LLM call < activity start-to-close < step < case; heartbeats on long activities |
| Bad output | Schema validation, one repair attempt, then a human gate; never pass unvalidated output downstream |
| Silent model change | Pin model versions; run the evaluation set on every model or prompt change; alert on drift in gate rates |
| Cost runaway | Retry budget per case (attempts × calls); a hard spend cap per case; cache responses by input hash so a retry or replay does not pay twice |
| Poison input | Check size and page count at intake; reject early with a clear reason; never retry bad input |
| Duplicate work | Deterministic IDs, idempotency keys, intent rows before side effects |
| Bad release | Versioned activities, a canary on a small share of cases, quarantine and pin back |

**One Temporal fact to remember:** when no retry policy is passed, Temporal retries an activity with no attempt limit, waiting 1 s and doubling up to 100 s between tries. So a raised bad-input error retries forever unless something sets a limit.

## Prompts 07 and 09: deployment, scale and operations

07 merges the old 07 and 08; 09 merges the old 09 and 14. Both read config files more than code, so Sonnet at medium effort is enough.

### 07 — Deployment and scale

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.
Refer to, do not repeat: 04 scenarios A, B, C and O (pod kill, lock and KEDA,
outage herd, local-path handoff) and 04 B6.

Topic: How Helix is deployed and scaled, and whether the scaling design matches
where the real bottlenecks are.

Read:
- infra/helm/agents-worker/ (templates and all values-*.yaml), infra/helm/identity-policy/values.yaml,
  infra/helm/_partials/ (all), infra/k8s/, infra/README.md
- agents/Dockerfile, plus the Dockerfiles of trigger_intake_svc, trigger_gateway_svc,
  cell_router_svc and registry_svc
- services/docker-compose.yaml, docker-compose.dev.yaml
- agents/src/agents/perf/ (all), agents/scripts/run_load_test.sh, agents/tests/perf/
- docs/spec/*agent-deployment-option-a*, docs/implementation/platform-at-scale-topology.md,
  docs/implementation/12-agent-deployment-option-a-implementation.md
- docs/spec/*azure-technology-stack* (service list only)
- docs/adr/ 0013, 0014, 0016, 0020, 0024 (Decision only)

Answer:
1. Deployable units table: image, base image, port, Helm chart (or none), image tag policy.
2. agents-worker chart: resources, probes (what liveness and readiness check), env,
   secrets source, service account and workload identity, PodDisruptionBudget,
   ephemeral-storage limits, and how one chart deploys two pools. [NOT FOUND] for missing items.
3. values-dev, staging, prod and dummy: what differs. Table.
4. KEDA: scaler type, query, thresholds, min and max per environment. Who emits
   temporal_activity_task_queue_backlog (Temporal server metrics, an exporter, nothing)?
5. Capacity math: each pool's prod max replicas x threads = maximum concurrent activities.
   Compare with what Azure OpenAI and Azure DI can serve (quota numbers if documented,
   else [NOT FOUND]). Is the LLM pool's max replicas bounded by provider quota anywhere?
6. How Temporal is hosted: local (compose), dev cluster (temporal-frontend.dev...), and
   the design (one cluster per cell, persistence store). What is decided vs open.
7. Cells, control plane, data plane and namespace isolation (ADR 0014, 0020, 0024):
   plain explanation with one diagram.
8. "Agent deployment option A": what it is, why temporary, what replaces it.
9. Azure services table: service, purpose, built or designed.
10. Load test: what it sends, what it measures, committed results ([NOT FOUND] if none).
11. With no CD workflow, how would a change reach AKS today? [NOT FOUND] if undocumented.

Write the result to helix-study/07-deploy-scale.md
```

### 09 — Operations: observability, audit, CI/CD

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.
Already known (FACTS, 04 B4): no alert rules, Cell Router metrics never recorded, no
telemetry in agents, Gateway logs via basicConfig, agent cores print. Do not re-check these.

Topic: Operating Helix - the designed observability and audit, alerts, CI/CD and supply chain.

Read:
- infra/observability/ (all)
- services/audit_svc/src/audit_svc/migrations/versions/ (both files)
- services/cell_router_svc/src/cell_router_svc/metrics.py (metric names and types only)
- .github/workflows/ (all 7 files), .github/actions/setup-opa/action.yml, .github/CODEOWNERS
- docs/spec/*global-audit-index-observability-design*, *observability-metrics-data-model-design*,
  *arize-agent-observability-design*, *vendor-agent-telemetry-contract-design*,
  *supply-chain-cicd-gate-design*, *sbom-supply-chain* (summary and decisions only)
- docs/implementation/08-*

Answer:
1. The designed observability stack: what each spec adds (metrics data model, Arize, global
   audit index, vendor telemetry contract). One table: piece, purpose, built or not.
2. The 11 Cell Router metrics: name, type, and what each would show if recorded.
3. The Fluent Bit vendor-agent filter: what it does and why.
4. Audit design: audit_log, outbox, poller, Event Hub, index. What is built?
   Why an outbox? Explain the dual-write problem simply.
5. Arize: what the design sends, and how PHI is kept out.
6. Debug walkthrough: "case X produced a wrong annotation" - what you can use today,
   and what the design adds.
7. [IDEA] The minimum alert set for launch, mapped to 04's scenarios: name, condition,
   threshold, and the scenario it catches.
8. Each GitHub workflow in one table: trigger and paths, jobs, what is tested,
   image registry, tag, auth (OIDC or secret).
9. The setup-opa action and the three identity-policy workflows as one policy pipeline.
10. Supply-chain gate and SBOM: designed vs built. What stops a bad change today?
11. Status table: logging, metrics, tracing, dashboards, alerts, LLM observability,
    audit, CI, CD - [CODE] / [DOCS-ONLY] / [NOT FOUND].

Write the result to helix-study/09-operations.md
```

## Prompts 10, 12 and 13: security, catalog and the LLM layer

13 matters most for an AI/ML role, so run it before the other two. 12 merges the old vendor and registry prompts.

### 13 — LLM and model layer

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.
Refer to, do not repeat: 02 sections 4c and 8a (agents, gate rules, thresholds);
04 scenarios G-L and B2 (LLM timeouts, 429s, outages, bad output, model drift,
page limit, retry budget).

Topic: The LLM and model layer - prompts, models, credentials, and how quality is measured.

Read:
- agents/src/agents/activities/segmentation_agent/core/src/pipeline.py: only the mapping and
  judge prompt builders and the embedding call (search: prompt, judge, embed, temperature, system)
- agents/src/agents/activities/logo_agent/core/logo_agent.py: the vision prompt builder only
- agents/src/agents/activities/ntdc_agent/core/NTDC_Agent/llm.py: the prompt builders only
- bisu_agent core: the Gemini / Vertex AI review prompt, and configs/thresholds.json
- agents/src/agents/legacy_compat/ (how keys and endpoints reach core code)
- docs/agents/UAIS_AGENT_MODEL_PORTING_GUIDE.md, docs/agents/2026-10-16-uais-connector-*
- agents/notebooks/uais_model_connectivity_report.ipynb (markdown cells and result summary only)
- services/libs/helix_platform_libs/src/helix_platform_libs/evaluation_framework/
  (metrics.py function list and docstrings; catalog.py)
- docs/spec/*annotated-pdf-metrics-backend-design*,
  docs/implementation/12-agent-metrics-hitl-gating-guideline.md
- docs/adr/0007-*.md (full)

Answer:
1. Table of every model call site: agent, purpose (mapping, judge, vision, review,
   embedding, OCR), provider and model or deployment name, temperature, file and line.
2. One real prompt per call type: what it asks, what it expects back, and one weakness
   [IDEA]. Quote max 10 lines each.
3. Where prompts live and how they are versioned (hard-coded, config, prompt_text
   overrides, Registry prompt_versions). Why are prompt_bindings ignored?
4. Credentials and endpoints today (legacy_compat, config.json, env vars, hard-coded URLs),
   and what changes with UAIS or the LLM broker.
5. UAIS: what it is, what porting required, what the connectivity report found.
6. ADR 0007: why regulated translation stays human (MCS) - the risk reasoning.
7. The LLM judge in segmentation: what it scores, how strict_accuracy is computed, and
   whether a judge from the same model family can be trusted [IDEA].
8. Quality measurement: what the evaluation framework and the metrics backend compute;
   which numbers are real and which are proxies; how the thresholds in 02 section 8a were
   chosen ([NOT FOUND] if there is no calibration data or gold set).
9. [IDEA] An evaluation plan an AI/ML lead would accept: gold-set size and labels, metrics
   per agent, setting thresholds from data, detecting drift (see 04 K).
10. Cost per document: model calls per agent for a 20-page pair, with the price data the
    code uses (DI price, token prices if any). Real numbers only.
11. Why segmentation, which calls GPT-4.1 and Gemini, sits on the deterministic queue,
    and what that does to KEDA scaling of both pools.

Write the result to helix-study/13-llm-layer.md
```

### 10 — Security and the trust boundary

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.
Refer to, do not repeat: 04 Q (broker error handling), 04 E (intake dedup).

Topic: Security in Helix - identity policy, brokers, capability tokens, PHI and secrets.

Read:
- services/identity_policy/ (code, .rego files, Rego tests), infra/helm/identity-policy/values.yaml
- services/trust_boundary/memory_broker/ (api/app.py, token check, quota, migrations)
- services/trust_boundary/phi_broker/ migrations (both)
- services/libs/helix_platform_libs/src/helix_platform_libs/content_reference.py
- broker_clients.py (token code, L22-L69)
- services/trigger_intake_svc/src/trigger_intake_svc/config.py and api/status.py (auth only)
- agents/src/agents/legacy_compat/ and each agent's core config files (secrets and endpoints only)
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
6. Where PHI rests today (local disk under /tmp, logs, Temporal history, in-memory blobs)
   vs where the design allows it. Table.
7. Secrets and endpoints in code and config: hard-coded URLs, key files, AZURE_* settings.
   List each with its risk; never print secret values.
8. Crypto-shredding, retention and legal hold (ADR 0021) in plain words, and the
   phi_broker tables that support them.
9. Row-level security: which tables use it, and how app.tenant_id is set.
10. Intake auth off by default, unauthenticated status endpoint, DNS-rebinding gap
    in pull mode: each risk in simple words.
11. Security controls designed but not built: list, ranked by risk.

Write the result to helix-study/10-security.md
```

### 12 — Registry, version pinning and the vendor kit

```text
Follow #file:helix-study/STYLE.md. Known facts: #file:helix-study/FACTS.md.
Refer to, do not repeat: 04 P (recall and quarantine) and 02 Q9 (versions).

Topic: The platform catalog - Registry, version pinning, and the vendor kit.

Read:
- services/registry_svc/src/registry_svc/ (routers, store, events, domain) and its migrations
- vendor-kit/ (schemas, src/helix_vendor_kit/conformance, harness, reference_agent -
  entry files only)
- docs/vendor-integration/vendor-development-kit-technical-guide.md (sections 1-4)
- docs/adr/ 0002, 0005, 0008, 0010, 0018, 0025, 0027 (Decision only)

Answer:
1. Registry endpoints table: method, path, purpose. Catalog tables and key columns.
2. resolve-pins: input, output, rules. How a case gets fixed versions of agents,
   prompts, rules and connectors.
3. Explicit repinning, no auto-adopt (ADR 0008): why safety over freshness.
4. Registry events on Service Bus (registry-events): which events, and who consumes them.
5. Shared rule library vs a BRMS (ADR 0005); shared library references (ADR 0010).
6. Vendor kit: the four schemas, SDK, conformance tests, harness and reference agent -
   what each does.
7. Vendor onboarding from code to production, every gate (ADR 0025, 0027).
8. Internal agent vs vendor agent: invocation differences, as a table.
9. [IDEA] What it would take for a pin to actually select the code that runs
   (versioned activity names, Worker Versioning, image digests).

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
Reuse instead of re-reading: 00-big-picture.md section 11 (Q7 table);
00t-temporal-primer.md part 10 (ADR 0011, 0019); 01-orchestration.md sections 7.9 and 9
(ADR 0004, 0006, 0012, 0020, 0023); 02-agents-layer.md section 3 (ADR 0011 in practice);
04-failure-recovery.md P and B1 (ADR 0022, 0029, error taxonomy).

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
8. Where a sound decision met weak implementation (for example ADR 0019 vs local-path
   handoff, ADR 0022 vs no pin check): one table.

Write the result to helix-study/15-tradeoffs.md
```

### 16 — Interview cheat sheet (run last)

Before running 16, copy the whole Corrections section of this doc into `helix-study/CORRECTIONS.md`. The cheat sheet then cannot repeat an error a study file contains.

```text
Follow the Language and Truth rules in #file:helix-study/STYLE.md.
Known facts: #file:helix-study/FACTS.md. Corrections: #file:helix-study/CORRECTIONS.md.
Where a study file conflicts with CORRECTIONS.md, CORRECTIONS.md wins.
Read only: sections 1, 4, 9 and 10 of each numbered file; the interview questions of
00t-temporal-primer.md; and from 04-failure-recovery.md the "Interview answer" lines,
B5, B6 and its Interview Q&A. Nothing else.

Write:
1. 30-second pitch: what Helix is, why it is built this way, and its honest status
   (a design-led platform, partly built).
2. A 2-minute walkthrough I can say out loud, following one case end to end and
   saying clearly which parts are built and which are designed.
3. One Mermaid diagram of the whole system, max 15 boxes, built vs designed marked.
4. The 30 hardest interview questions across all files: 3-5 sentence answers,
   one file reference each.
5. A 60-second answer to "How does your system survive failures?"
6. Numbers I can quote: real values only, with source.
7. Do-not-claim list: everything [DOCS-ONLY] or [NOT FOUND], plus every item in CORRECTIONS.md.
8. Ten trade-off one-liners: "We chose X over Y because Z; the cost is W."
9. Gaps I can discuss honestly, and how I would close the top 3.

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
