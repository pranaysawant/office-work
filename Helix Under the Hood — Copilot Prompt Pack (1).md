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
3. Create `helix-study/STYLE.md` and paste the block from the next section.
4. In Copilot Chat, switch to **Agent** mode so it can open files and write the .md file.
5. In the model picker, choose the strongest model available to you.
6. If `#file:` does not attach a file, type `#` and pick the file from the list.
7. If Mermaid diagrams show as code, install the "Markdown Preview Mermaid Support" extension.

Paths come from your folder screenshots. Where a name was cut off, the prompt uses `*` and Copilot searches for it. The notes contain internal design details, so keep `helix-study/` on the work laptop.

**Run order**

| # | Output file | Topic | Priority |
| --- | --- | --- | --- |
| 00 | 00-big-picture.md | What Helix is, every service, one case end to end | Must |
| 01 | 01-orchestration.md | Temporal workflow, config-driven flow, dispatch | Must |
| 02 | 02-agent-anatomy.md | Inside one agent; worker and registry | Must |
| 03 | 03-contracts-handoff.md | How agents pass data; contracts; PHI by reference | Must |
| 04 | 04-failure-recovery.md | Retries, crashes, idempotency, bad versions | Must |
| 05 | 05-human-review.md | Gates, review console, timeouts | Should |
| 06 | 06-ingress.md | Trigger gateway, intake, case ID | Should |
| 07 | 07-deployment.md | AKS, Helm, KEDA, cells, Azure services | Must |
| 08 | 08-scale-cost.md | Bottlenecks, load tests, LLM cost | Should |
| 09 | 09-observability.md | Logs, traces, audit, debugging a wrong output | Must |
| 10 | 10-security-phi.md | OPA, brokers, tokens, PHI, retention | Should |
| 11 | 11-vendor-agents.md | Vendor kit, onboarding, isolation | Should |
| 12 | 12-registry-versioning.md | Catalogs, version pinning, recall | If time |
| 13 | 13-llm-layer.md | Model gateway, prompts, quality measurement | Must |
| 14 | 14-cicd.md | GitHub workflows, tests, what is missing | Should |
| 15 | 15-tradeoffs.md | All 33 ADRs, reviews, open decisions | Must |
| 16 | 16-cheat-sheet.md | Pitch, hardest questions, do-not-claim list | Must, run last |

**For every topic file**

1. Run the topic prompt.
2. Run the fact-check prompt (last section) on the new file.
3. Read it top to bottom. Stop at the first part you don't understand and use the follow-up prompt on that one piece.
4. If Copilot stops halfway, say: `Continue. Write the missing sections.`

Agent mode shows every file change for you to keep or undo. Accept only changes inside `helix-study/`.

## STYLE.md — the rules every output follows

Paste this once into `helix-study/STYLE.md`. Every prompt points to it, so each prompt stays short and every output has the same shape. The truth rules stop Copilot from guessing. The altitude sections build each topic from a plain idea down to exact code, with numbers held back until section 8.

```text
# Writing rules for Helix study notes

## Reader
- The reader is me: a senior AI/ML engineer preparing for interviews. English is my second language.
- After reading, I must be able to explain this out loud to a CTO.

## Language
- Simple English. Short sentences, under 20 words. Active voice.
- Define every technical term in one plain line the first time it appears.
- Do not use these words unless the same sentence says HOW, with a file reference:
  robust, seamless, leverages, facilitates, ensures, comprehensive, scalable,
  efficient, various, handles, manages, powerful, flexible.
- No marketing tone. No filler. If the code is unclear, write "Unclear" and say why.

## Truth rules (most important)
- Open and read every file you use. Never answer from file names alone.
- Every factual claim ends with evidence: path/to/file.py:L120-L145, or a doc path.
- Tag every claim:
  [CODE]      = implemented, seen in code or config
  [DOCS-ONLY] = described in docs, specs or ADRs, not found in code
  [NOT FOUND] = searched for it, not present
- Never invent numbers, names, settings or behaviour. Copy real values
  (timeouts, retries, replicas, thresholds, model names) with the file reference.
- When code and docs disagree, show both and say which is true today.

## Shape of every file (these headings, in this order)
1. One-line answer: the whole topic in one sentence.
2. Altitude 30,000 ft (the idea): 3-5 sentences. No technical terms, no numbers.
   What problem exists, and what Helix does about it.
3. Why it is built this way: start from the simplest naive design. Say why it
   breaks. Then add each piece Helix uses, one at a time, and the problem each
   piece solves. Cite ADRs.
4. Altitude 10,000 ft (the pieces): for each component write
   What it is / Why it exists / How it works, 2-4 lines each.
5. Altitude 1,000 ft (step by step): numbered steps for ONE real example.
   Each step: what happens, which file and function, data in, data out.
   Use real field names from payload_template.json files or test fixtures.
6. Diagram: Mermaid. sequenceDiagram for flows, flowchart for structure.
   Max 12 boxes. Plain-English labels.
7. Code walkthrough: the 3-5 most important snippets, max 15 lines each.
   After each snippet, explain only the important lines.
8. Exact settings: table Setting | Value | File. Real values only.
9. Evidence table: Claim | Tag | Evidence.
10. Weak points and open gaps: what is missing, fragile, or only designed.
    Use docs/reviews and docs/implementation/pending-decisions.md where relevant.
11. Interview Q&A: answer every question listed in the prompt.
    Each answer 3-6 sentences, factual ("In Helix, ..."), with one file reference.
    Then add the 2 follow-up questions a CTO would ask next, with answers.
12. Glossary: every term used, one line each.
13. Files read: list every file you opened.

## Hard limits
- Write only inside the helix-study/ folder. Do not edit, create or delete any other file.
- Do not run commands that change anything (no installs, no git commands, no deploys).
- If the output gets long, write it section by section until all 13 sections exist.
```

## Prompts 00–03: architecture and orchestration

These four files carry most of the interview. Run them first, in order, because later prompts assume you know the case flow.

### 00 — Big picture

A CTO starts here to check whether you see the whole system before the details.

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: Helix big picture - what it is and how one case flows end to end.

Read first:
- AGENTS.md, docs/index.md, docs/implementation/00-repo-structure.md
- docs/implementation/case-flow-walkthrough.md
- docs/AGENT_INVOCATION_UNIFIED_FLOW.md, docs/INTERNAL_AGENT_DEPLOYMENT_AND_INVOCATION_*.md
- services/docker-compose.yaml, docker-compose.dev.yaml
- the entry point (main, app or server file) of every folder in services/

Answer these interview questions:
1. What business problem does Helix solve? What exactly is a "case"?
2. List every service in services/ plus the agents worker. For each: one-line job,
   framework, how it is called (HTTP, gRPC, Temporal), and what it stores.
3. Follow one document from upload to final result. Name every hop, service,
   protocol and data store.
4. Where does Temporal sit, and which parts of the system talk to it?
5. Build-status table for each service: code exists? tests? Helm chart?
   GitHub workflow? Use the tags [CODE] / [DOCS-ONLY] / [NOT FOUND].
6. How is Helix different from a simple script that calls agent A, then B, then C?
7. Which problems of simpler designs do the docs say Helix solves?
   If the docs do not say, write [NOT FOUND].

Write the result to helix-study/00-big-picture.md
```

### 01 — Orchestration

The core question: who decides which agent runs next, and what keeps a case alive when something dies.

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: How Helix orchestrates agents with Temporal.

Read first:
- services/orchestrator_svc/ and services/cell_router_svc/ (all files)
- services/MCS_workflow_config_v1.json, vendor-kit/schemas/workflow-config.schema.json
- docs/spec/*generic-orchestrator-workflow-design*, docs/spec/*cell-router-workflow-directory-design*,
  docs/spec/*aks-temporal-distributed-architecture*
- docs/implementation/03-*, docs/implementation/04-*, docs/TEMPORAL_CAPABILITIES_HELIX_PLATFORM.md
- docs/adr/ files 0004, 0011, 0013, 0029, 0031, 0032

Answer these interview questions:
1. Where is the workflow defined (search @workflow.defn)? Show the run method
   and explain it line by line.
2. Is the order of agents hard-coded or read from config? Walk
   MCS_workflow_config_v1.json field by field and show the code that reads each field.
3. Do steps run only in sequence, or also in parallel or with conditions?
   Show the code for each case that exists.
4. How does the workflow call an agent: execute_activity, child workflow, or other?
   Task queue names, timeouts and retry policy, with exact values.
5. Who starts the workflow, with what workflow ID and what input?
   Where is the case ID created?
6. What does cell_router_svc decide? What is the "workflow directory"?
7. Why one generic workflow instead of one workflow per use case? What does it cost?
8. ADR 0011 says agent loops run in-process, not as durable sub-orchestrations.
   Explain in simple words. What is lost if a pod dies in the middle of a loop?
9. Temporal workflow code must be deterministic. How does this code keep time,
   randomness and network calls out of the workflow? How are workflow code
   changes rolled out while old cases are still running (patching or versioning)?
10. Why Temporal instead of a queue plus database, Azure Durable Functions or
    LangGraph? Answer only from ADRs and specs; if not discussed, write [NOT FOUND].

Write the result to helix-study/01-orchestration.md
```

### 02 — Agent anatomy

Interviewers ask you to open one agent and explain every part, then how agents get onto machines.

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: What is inside one Helix agent, and how agents run on workers.

Read first:
- agents/src/agents/activities/segmentation_agent/ (every file and subfolder)
- agents/src/agents/activities/agent1_dummy_agent/ and agent2_dummy_agent/
- agents/src/agents/registry.py, agents/src/agents/worker.py,
  agents/src/agents/io_models/base.py, agents/src/agents/legacy_compat/
- agents/README.md, agents/Dockerfile, agents/pyproject.toml
- docs/agents/AGENT_LAYER.md, docs/spec/*core-agent-activity-framework-design*,
  docs/implementation/11-*, docs/reviews/*core-agents-temporal-framework-review*

Answer these interview questions:
1. Explain each part of segmentation_agent: activity.py, core/, data_model/,
   mappers.py, contract/, payload_template.json. Why is an agent split this way?
2. Trace one input from payload_template.json to the output, with real field names.
3. What does registry.py do? How does a new agent get registered?
4. What does worker.py do at start-up? Task queue names, concurrency limits,
   which activities it registers, graceful shutdown. Exact values.
5. Do all agents run in one worker process and one image, or separately?
   What are the consequences of that choice?
6. Table of every agent in activities/: purpose, input, output,
   uses an LLM (yes/no and where), external services called.
7. What do the agent names mean in the code (for example bisu, ntdc)?
   If the code does not explain a name, write [NOT FOUND].
8. What do the dummy agents show? List the steps to add a new agent.
9. What is legacy_compat for?
10. What did the 2026-10-06 framework review criticise, and is it fixed in code?

Write the result to helix-study/02-agent-anatomy.md
```

### 03 — Contracts and handoff

This answers "how do your agents communicate", which every multi-agent interview asks.

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: How Helix agents pass data to each other.

Read first:
- agents/linguistic-agent-contract.json, agents/src/agents/io_models/base.py
- the contract/ folder and mappers.py of every agent in agents/src/agents/activities/
- vendor-kit/schemas/agent-contract.schema.json, vendor-kit/schemas/agent-manifest.schema.json
- agents/tests/contract/
- the orchestrator code that passes one activity's result to the next (services/orchestrator_svc/)
- docs/adr/ files 0008, 0012, 0019, 0030, 0033; docs/spec/*memory-broker-design*

Answer these interview questions:
1. Do agents ever call each other directly? If not, who moves data between them?
2. Explain linguistic-agent-contract.json field by field. Who must follow it?
3. Explain the shared envelope in io_models/base.py field by field.
4. When agent A finishes, what exactly does agent B receive: the full output,
   an ID, or a pointer to storage? Show the code.
5. Where is output checked against its declared type (ADR 0012)? Pydantic,
   JSON Schema or both? What error happens on a mismatch, and what does the
   workflow do with it?
6. How are contracts versioned (contract_version)? What happens if agent A
   changes its output while agent B expects the old format?
7. PHI by reference (ADR 0019, 0030): what is passed instead of document content?
   Who turns the reference back into content, and who is allowed to?
8. What is the memory broker (ADR 0033)? What do agents store or read through it?
9. What do the contract tests check, and what would they miss?
10. Draw one sequence diagram: agent A output -> validation -> storage or
    reference -> agent B input.

Write the result to helix-study/03-contracts-handoff.md
```

## Prompts 04–06: reliability, human review and ingress

Senior panels spend the most time on failure. Prompt 04 is scenario-based on purpose: a CTO asks "what happens when X dies", not "explain your retry policy".

### 04 — Failure and recovery

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: What happens when things fail in Helix, and how it recovers.

Read first:
- services/orchestrator_svc/, agents/src/agents/worker.py,
  every agents/src/agents/activities/*/activity.py
- vendor-kit/schemas/error-taxonomy.json
- services/libs/ (search: retry, timeout, idempot, heartbeat, error)
- docs/adr/ files 0008, 0022, 0023, 0029; docs/reviews/;
  docs/implementation/pending-decisions.md

For each scenario, write: what happens step by step, which code runs,
and the final state of the case. Tag every step.
A. An LLM call inside an agent times out.
B. An agent raises an unexpected exception.
C. An agent returns output that fails validation.
D. A worker pod is killed in the middle of an activity.
E. The orchestrator pod is killed in the middle of a workflow.
F. The Temporal server is unavailable for 5 minutes.
G. The same document is submitted twice.
H. A broker (PHI or memory) is down.
I. A bad agent version is deployed and starts producing wrong results.
J. A human reviewer never acts on a gate.

Then answer these interview questions:
1. Retry policy per activity: initial interval, backoff, max attempts,
   non-retryable error types. Exact values.
2. How does error-taxonomy.json decide retryable vs not? Show where code uses it.
3. Where is the case ID minted (ADR 0029)? How does each activity stay safe to
   retry (no duplicate writes, no duplicate side effects)?
4. Are heartbeats used for long activities? Values?
5. Is there compensation or rollback? List every terminal state a case can end in.
6. ADR 0022 recall and quarantine: who triggers it, and what happens to
   cases already running?
7. Which failure is NOT handled today? Be specific.

Write the result to helix-study/04-failure-recovery.md
```

### 05 — Human review

Regulated healthcare work always has a human gate, so expect "when does a human step in, and what if they don't".

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: Human-in-the-loop review in Helix.

Read first:
- services/gate_svc/, services/review_console_svc/
- orchestrator code that waits for a human decision
  (search: signal, update, wait_condition, gate)
- docs/spec/*hitl-human-in-the-loop-review-specification*,
  docs/spec/*gate-service-review-console-design*
- docs/implementation/06-*, docs/implementation/07-hitl-*,
  docs/implementation/12-agent-metrics-hitl-gating-guideline.md
- docs/adr/ files 0003, 0006, 0023

Answer these interview questions:
1. When does a case go to a human: every case, rules, confidence scores or
   metric thresholds? Exact rules and values.
2. How does the workflow wait for the human: Temporal signal, update, polling,
   or a new workflow? Show the code.
3. gate_svc vs review_console_svc: what does each own? What does the reviewer see?
4. How does the reviewer's decision get back into the running workflow?
5. What if no one reviews (ADR 0023 terminal disposition)? Timeout values?
6. Who is assigned a review (ADR 0006 static assignment)? Why no capacity engine?
7. ADR 0003: why is the review console the "system of record"?
8. How are human decisions stored, for audit and for improving agents later?

Write the result to helix-study/05-human-review.md
```

### 06 — Ingress: trigger gateway and intake

The front door: how work arrives, who is allowed in, and how duplicates are stopped.

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: How work enters Helix - trigger gateway and intake.

Read first:
- services/trigger_gateway_svc/ and services/trigger_intake_svc/ (all files, including tests)
- .github/workflows/trigger-*.yml
- docs/spec/*trigger-gateway-document-intake-design*, docs/implementation/10-*
- docs/adr/ files 0028, 0029, 0031, 0032

Answer these interview questions:
1. What API endpoints exist? Request and response shape of each, real field names.
2. How is the caller authenticated and authorised? Where does OPA come in?
3. Lane A vs lane B (ADR 0028): what is each lane for, and why split them?
4. Where is the uploaded document stored? What travels further: the file or a reference?
5. Where is the case ID minted, and how does it make repeated submissions safe?
6. How does intake start the workflow: gRPC, Temporal client or other
   (ADR 0031, 0032)? Show the code.
7. What protects the system from overload: rate limits, size limits,
   back-pressure? Exact values or [NOT FOUND].
8. What does the caller get back, and how do they learn the final result
   (polling, callback, event)?

Write the result to helix-study/06-ingress.md
```

## Prompts 07–09: deployment, scale and observability

These cover "how does it run in production". Since Helix has no CD workflow, prompt 07 asks Copilot to find out how changes reach AKS today rather than assume.

### 07 — Deployment and runtime topology

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: How Helix is deployed and runs on Azure.

Read first:
- infra/ (every file: helm/_partials, helm/agents-worker, helm/identity-policy,
  k8s/, observability/, README.md)
- agents/Dockerfile, every Dockerfile under services/,
  services/docker-compose.yaml, docker-compose.dev.yaml
- docs/spec/*aks-temporal-distributed-architecture*, *azure-technology-stack*,
  *azure-starter-service-configuration*, *aks-concepts-primer*, *agent-deployment-option-a*
- docs/implementation/12-agent-deployment-option-a-*,
  docs/implementation/platform-at-scale-topology.md
- docs/INTERNAL_AGENT_DEPLOYMENT_AND_INVOCATION_*.md
- docs/adr/ files 0013, 0014, 0016, 0020, 0024

Answer these interview questions:
1. Table of every deployable unit: image, Helm chart (or none), namespace, replicas.
2. Walk the agents-worker chart:
   deployment.yaml - resources, probes, env vars, where secrets come from;
   scaledobject.yaml - scaler type, metric, min/max replicas, polling, cooldown;
   serviceaccount.yaml - is Azure workload identity used?
   Exact values.
3. Table: what differs between values-dev, values-staging, values-prod and values-dummy.
4. Is Temporal self-hosted on AKS or Temporal Cloud? Where is its config?
   Which database stores its history?
5. Table of Azure services used: service, purpose, file or doc.
6. What is a "cell"? What runs in the control plane vs the data plane?
   How many cells, and how is a case pinned to one?
7. What is "agent deployment option A"? Why is it called temporary?
   What is the target option?
8. How do secrets and model credentials reach the pods?
9. Local development: what does docker-compose start? How do you run one agent locally?
10. There is no CD workflow in .github/. How does a change reach AKS today?
    If not documented anywhere, write [NOT FOUND].

Write the result to helix-study/07-deployment.md
```

### 08 — Scaling, performance and cost

Expect "what happens at 10x load" and "where does the money go". Only real numbers count; the prompt forbids invented ones.

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: How Helix scales, where it slows down, and what it costs.

Read first:
- infra/helm/agents-worker/templates/scaledobject.yaml and all values-*.yaml
- agents/src/agents/worker.py, agents/src/agents/perf/, agents/tests/perf/,
  agents/scripts/run_load_test.sh
- docs/implementation/platform-at-scale-topology.md,
  docs/agents/UAIS_AGENT_MODEL_PORTING_GUIDE.md
- the LLM client code used by agents (search: uais, openai, chat, completion, tokens)

Answer these interview questions:
1. What scales automatically, on what signal, between which limits?
2. How many activities can one worker run at once? Exact settings.
3. Where is the bottleneck: LLM rate limits, Temporal, CPU, a broker,
   the database? Show evidence.
4. What does the load test do? What numbers exist (throughput, latency per
   agent, time per document)? Real numbers only, else [NOT FOUND].
5. Which agents run in sequence and which in parallel?
   What is the critical path for one document?
6. LLM usage: model per agent, tokens per call if logged, any caching or batching.
7. Based on the code and settings, what breaks first at 10x load?
8. What cost or usage metrics exist today, in code or in specs?

Write the result to helix-study/08-scale-cost.md
```

### 09 — Observability and debugging

The classic test: "the output for case X is wrong, show me how you find out why". Question 7 forces a real debugging walkthrough.

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: Observability - how you see and debug what Helix is doing.

Read first:
- infra/observability/ (fluent-bit-vendor-agent-filter.yaml, README.md)
- services/audit_svc/; services/libs/ and agents/src/agents/
  (search: logging, logger, otel, opentelemetry, trace, span, metric, arize)
- docs/spec/*global-audit-index-observability-design*,
  *observability-metrics-data-model-design*, *arize-agent-observability-design*,
  *vendor-agent-telemetry-contract-design*, *annotated-pdf-metrics-backend-design*
- docs/implementation/08-*

Answer these interview questions:
1. Logs: format, fields, destination. Does every log line carry case ID and workflow ID?
2. What does the Fluent Bit vendor-agent filter do? Why do vendor-agent logs
   need special handling?
3. Tracing: is OpenTelemetry used? Temporal interceptors? Can one trace follow
   a case across services and agents?
4. Arize: what is sent (prompts, outputs, scores)? How is PHI kept out?
   Implemented or spec only?
5. Metrics: list every metric defined in code, and every metric only in specs.
6. Audit: what events does audit_svc record, where, and can they be changed or deleted?
7. Scenario: "The final output for case X is wrong." Walk through debugging it
   step by step with what exists today: Temporal event history, logs, traces,
   audit records, review console.
8. What does the vendor telemetry contract require from vendor agents?
9. Status table for logging, tracing, metrics, dashboards, alerts,
   LLM observability, audit: [CODE] / [DOCS-ONLY] / [NOT FOUND].

Write the result to helix-study/09-observability.md
```

## Prompts 10–13: security, vendors, versioning and the LLM layer

These separate a senior answer from a mid-level one. Prompt 13 matters most for an AI/ML role: models, prompts and how quality is measured.

### 10 — Security, identity and PHI

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: Security, identity and PHI protection in Helix.

Read first:
- services/identity_policy/ (all .rego and code files), infra/helm/identity-policy/,
  .github/actions/setup-opa/action.yml, .github/workflows/identity-policy-*.yml
- services/trust_boundary/ (all files)
- docs/spec/*identity-policy-design*, *trust-boundary-sandbox-brokers-design*,
  *memory-broker-design*, *database-schema-design*
- docs/implementation/02-*, docs/implementation/05-*
- docs/adr/ files 0015, 0018, 0019, 0021, 0024, 0026, 0030, 0033

Answer these interview questions:
1. What decisions does the OPA identity policy make? Show one real rule and
   explain it line by line. Who calls OPA, and when?
2. What is the trust boundary? List all brokers (ADR 0033 calls memory the
   fifth) and what each one brokers.
3. "No ambient authority" (ADR 0015): what does it mean in simple words,
   and how is it enforced?
4. Capability tokens: who mints them, what is inside, how long they live,
   how they travel (ADR 0026).
5. PHI: field minimisation, never in Temporal history, passed by reference.
   Show where each rule is enforced in code.
6. Retention, erasure, legal hold, crypto-shredding (ADR 0021): explain
   crypto-shredding simply. Is it implemented?
7. Where do secrets and encryption keys live? How do pods get them?
8. How is a vendor agent isolated from PHI and from other tenants
   (namespaces, network policy)?
9. Which security controls are only designed and not built yet?

Write the result to helix-study/10-security-phi.md
```

### 11 — Vendor agents

Hosting third-party agents is what makes Helix a platform rather than a pipeline, so expect "how do you trust code you didn't write".

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: How third-party vendor agents plug into Helix.

Read first:
- vendor-kit/ (docs, examples, reference_agent, schemas,
  src/helix_vendor_kit/conformance, harness)
- docs/vendor-integration/ (all), docs/helix-platform-vendor-agent-integration-guide.md,
  docs/AGENT_INVOCATION_UNIFIED_FLOW.md
- docs/spec/*vendor-development-kit-design*, *vendor-agent-telemetry-contract-design*
- docs/adr/ files 0002, 0018, 0025, 0026, 0027

Answer these interview questions:
1. Why does Helix support vendor agents, and what is out of scope (ADR 0002)?
2. What is in the vendor kit? Explain each part: SDK, schemas, reference_agent,
   conformance tests, harness, mock brokers.
3. Explain agent-manifest.schema.json and workflow-config.schema.json field by field.
4. Onboarding from "vendor starts coding" to "running in production":
   every step and approval gate (ADR 0025).
5. Table: internal agent vs vendor agent - how is invocation different?
6. Why must vendors use the platform SDK (ADR 0027)? What does the SDK hide?
7. What do conformance tests check? What can a vendor still get wrong?
8. What does the onboarding-difficulty assessment say are the hardest parts?
9. A vendor agent misbehaves in production. What can the platform do
   (quarantine, recall, revoke its token)?

Write the result to helix-study/11-vendor-agents.md
```

### 12 — Registry and versioning

The question behind this one: "how do you change an agent without breaking cases already running?"

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: Registry, catalogs and version control of agents and workflows.

Read first:
- services/registry_svc/ (all files), and any database migration or schema files under services/
- docs/spec/*registry-catalogs-design*, *database-schema-design*,
  docs/implementation/01-*
- docs/adr/ files 0005, 0008, 0010, 0022

Answer these interview questions:
1. What catalogs exist and what does each store? Show the database tables and columns.
2. How does a workflow choose which agent version to run?
3. Explicit repinning, no auto-adopt (ADR 0008): what does it mean,
   and why choose safety over freshness?
4. Emergency recall and quarantine (ADR 0022): exact steps, and what happens
   to running cases.
5. Shared rule library instead of a BRMS (ADR 0005): what rules live there,
   and why not a rules engine?
6. ADR 0010 shared library references: explain simply.
7. How is Temporal workflow code itself versioned while cases are running?

Write the result to helix-study/12-registry-versioning.md
```

### 13 — LLM and model layer

For an AI/ML role this is where the CTO digs deepest: which model, which prompt, and how you know the output is good.

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: The LLM and model layer - which models, how they are called,
how quality is measured.

Read first:
- agents/notebooks/uais_model_connectivity_report.ipynb,
  agents/notebooks/temporal_agents_independent_runner.ipynb
- docs/agents/UAIS_AGENT_MODEL_PORTING_GUIDE.md, docs/agents/2026-10-16-uais-connector-*
- every agents/src/agents/activities/*/core/ folder
  (search: prompt, model, temperature, uais, json_schema, response_format)
- docs/spec/*annotated-pdf-metrics-backend-design*,
  docs/implementation/12-agent-metrics-hitl-gating-guideline.md
- docs/adr/ file 0007

Answer these interview questions:
1. What is UAIS, and how do agents reach models through it?
   Auth, endpoint config, client code.
2. Table: agent, model, temperature, max tokens, structured output (yes/no).
3. Where do prompts live (code, files, registry)? Are they versioned?
   Show one real prompt and explain it.
4. How is LLM output parsed and validated? What happens on malformed JSON?
5. ADR 0007: why is regulated translation done by MCS and not by an LLM?
   Explain the risk reasoning.
6. Fallback models, rate-limit handling and retries at the LLM call level.
   Exact values.
7. How is agent quality measured: metrics, golden datasets, thresholds,
   the annotated-PDF metrics backend? Real numbers only.
8. What guards against hallucination or wrong output before a human sees it?
9. What did the porting guide say had to change when moving agents to UAIS?

Write the result to helix-study/13-llm-layer.md
```

## Prompts 14–16: CI/CD, trade-offs and the cheat sheet

Prompt 15 gives you the "why" behind every decision. Prompt 16 runs last and turns all earlier files into what you say in the room.

### 14 — CI/CD, tests and supply chain

```text
Follow every rule in #file:helix-study/STYLE.md.

Topic: CI/CD, tests and supply chain.

Read first:
- .github/ (every workflow file, actions/setup-opa/action.yml, CODEOWNERS)
- every pyproject.toml, and every tests/ folder in the repo
- docs/spec/*supply-chain-cicd-gate-design*, *sbom-supply-chain-to-review*,
  docs/implementation/07-supply-chain-*

Answer these interview questions:
1. For each workflow file: trigger (events and paths), jobs, steps, what is tested,
   where the image is pushed, how it is tagged, how it authenticates
   (OIDC or a stored secret).
2. What does the setup-opa action do? What do the three identity-policy
   workflows do together?
3. CODEOWNERS: who must approve which folders?
4. Coverage table for each service and the agents worker: test workflow?
   image build workflow? deploy workflow?
5. How are the agents-worker and orchestrator images built today?
   If not found, write [NOT FOUND].
6. List each test suite (unit, contract, activity, perf, service tests):
   what it covers, and the exact command to run it locally (uv, pytest).
7. SBOM and the supply-chain gate: what is designed, and what is built?
8. Today, what would stop a bad change from reaching production?

Write the result to helix-study/14-cicd.md
```

### 15 — Design decisions and trade-offs

CTOs probe decisions more than code: "why this, what did you reject, what did it cost". This prompt turns 33 ADRs into that.

```text
Follow every rule in #file:helix-study/STYLE.md. Sections 4-7 can be short
here; the ADR tables are the main content.

Topic: Design decisions and trade-offs - every ADR, the reviews, open decisions.

Read first:
- docs/adr/ (all 33 files and index.md)
- docs/reviews/ (all), docs/implementation/pending-decisions.md,
  docs/future_spec/ (all), docs/spec/CONTEXT.md

Answer these interview questions:
1. Table of all 33 ADRs: number, decision in plain words (one line), problem it
   solves, alternative rejected, cost of the decision.
2. The 8 ADRs a CTO is most likely to challenge. For each: the decision, the
   strongest argument against it, and the answer the ADR gives.
3. Which ADRs depend on each other? Draw a small Mermaid diagram of the main chains.
4. ADR 0009: what did the mock POC prove, and what did it not prove?
5. What did the review documents criticise? What changed after?
6. What is still undecided (pending-decisions, future_spec)? Why does each matter?
7. Which decisions would be hardest to reverse later, and why?

Write the result to helix-study/15-tradeoffs.md
```

### 16 — Interview cheat sheet (run last)

```text
Read every numbered file in helix-study/ (00 to 15). Follow the Language and
Truth rules in #file:helix-study/STYLE.md, but use this shape instead of the
13 sections:

1. 30-second pitch: what Helix is and why it is built this way.
2. 2-minute architecture walkthrough I can say out loud, following one case
   end to end.
3. One Mermaid diagram of the whole system, max 15 boxes.
4. The 30 hardest interview questions across all topics. Each with a 3-5
   sentence answer and one file reference.
5. Numbers I can quote: only real values found in the repo (timeouts, retries,
   replicas, agent count, ADR count). Table with source.
6. Do-not-claim list: everything tagged [DOCS-ONLY] or [NOT FOUND], so I never
   present a design as built.
7. Ten trade-off one-liners: "We chose X over Y because Z; the cost is W."
8. Gaps I can discuss honestly: what is missing, and why it matters.

Write the result to helix-study/16-cheat-sheet.md
```

## Utility prompts: single file, fact-check, follow-up

Use these alongside the topic prompts. The file deep-dive replaces "give me a 15,000 ft view of this file"; the fact-check catches Copilot's guesses before you learn them.

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
