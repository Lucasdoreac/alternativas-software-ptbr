---
name: personal-dev-harness
description: Apply or evolve Lucas's reusable development harness across personal, professional, organizational, and collaborative repositories, including agent configuration, project bootstrap, execution, and temporary-resource lifecycle. Use when establishing defaults for an existing or new repo; not for ordinary isolated code changes.
---

# Personal development harness

Treat the harness as a personal reusable platform with project adapters, not a set of copied per-repository instructions. The target covers Codex, Claude, and Antigravity where installed, macOS and Ubuntu, local repos and remotes, and projects created by SOBER. Apply policies only where Lucas has authority; collaboration or organization ownership does not imply permission to change collaborators' workflows.

> **SOBER host (2026-10-23):** the Lenovo Ubuntu is retired; SOBER is being rebuilt natively on the Mac. See the [host transition note](../../README.md#sober-host-transition--2026-10-23).

## Behavior claims and implementation evidence

A capability claim is an assertion about behavior, distinct from a file ownership
claim. Every capability claim in documentation, skills, reusable prompts, reports
and operator interfaces must match the executable implementation and evidence for
the scope it declares. Trace the claim through its real entrypoint, authorization,
dispatch, durable state, executor, effect, verification and receipt, including
parallel paths outside the main graph. Identify the source SHA, host/runtime and
effective configuration; a matching file, installed link or passing isolated test
does not prove runtime adoption.

Keep an approved requirement distinct from a claim of completed implementation.
If the requirement is unmet, preserve it as an implementation gap in the existing
canonical plan and repair the responsible code or adapter. Do not weaken or remove
the requirement merely to make documentation agree with incomplete code. Correct
unsupported completion claims immediately and retain accurate scope limits while
the repair proceeds. Evidence for one executor or host never closes another's gap.

Refactor divergent instructions at their canonical source, migrate consumers
through the existing installer/adapter and retire conflicting copies after
checking their actual consumers. Put mandatory transitions and protected
invariants in executable gates; prompts describe that interface. Use focused
regressions and revert-checks for behavior changes. Editing this contract alone
does not implement a reconciliation gate, scheduler, repair loop or rollout.

## Risk-adaptive engineering quality

Use the same quality contract for code, automation, agent tools, research,
reviews, documents, and operations, but select controls for the actual artifact
and risk. The contract is a set of principles, not a mandatory output template
or a checklist to repeat in every function.

- Before changing behavior, identify the trust boundaries, state, external
  effects, likely failure modes, recovery path, and evidence that will establish
  success. Record that compactly in the durable task/plan when work spans turns
  or has production effects; keep low-risk local work proportional.
- Validate external or untrusted input and authorization at trust boundaries;
  enforce domain invariants where state changes. Use types and schemas to make
  module contracts explicit, without duplicating identical checks at every
  internal call.
- Log meaningful state transitions and external effects with stable correlation
  IDs. Redact secrets, personal data, and private payloads; log only bounded
  evidence needed to diagnose and audit.
- Retry only classified transient failures, within an attempt/deadline budget,
  with backoff and idempotency appropriate to the effect. Reconcile an uncertain
  external effect before dispatching it again.
- Isolate providers, I/O, clocks, and other unstable dependencies behind
  replaceable adapters when this enables real tests, recovery, or provider
  changes. Do not add dependency injection or abstraction without a concrete
  boundary to isolate.
- Choose applicable NFRs from security/privacy/authorization, correctness/data
  integrity, tenant isolation, availability/recovery, observability/operations,
  migration/rollback, portability/supply chain, and resource/cost limits. State
  why a material dimension is out of scope; do not add code solely to satisfy a
  generic checklist.
- Test observable outcomes and failure boundaries in proportion to risk.
  Agentic or probabilistic behavior also needs reproducible multi-step
  evaluations that verify tool use and resulting state, not just final prose.
  Run focused checks with each implementation slice; run the complete canonical
  production suite once per deployed SHA.
- Deliver the artifact and evidence suited to the task. Research, review,
  documentation, operations, and software each have different completion
  criteria; do not require every task to return code and a test example.

The canonical plan is the only release decision record. It records scoped grants
and action evidence; standing owner grants remove repeated confirmation for
actions within their scope. Executors proceed automatically when the grant and
that action's plan gate allow it. GitHub Actions do not gate these decisions;
when a repository requires a status, it is the exact-SHA `sober/local-ci`
receipt from the canonical post-deploy run.

## First-class tools

A capability that a person or an agent uses more than once ships as a tool, not a loose script: a `tool.toml`
manifest, install and launcher, local human UI, deterministic CLI, API or MCP for agents, health check, metrics and
real-use evidence, all over one core. Channels such as WhatsApp only call that contract. Remote access is private
(Tailscale Serve); public exposure (Funnel) needs an explicit owner grant and scope. Contract, measured reference
(Asset Studio + OpenToonz) and checker: [references/first-class-tools.md](references/first-class-tools.md),
`scripts/tool_manifest_check.py`.

## Agent and workflow boundaries

- Give each worker a bounded mission: typed inputs/outputs, allowed tools,
  authority scope, resource/deadline budget, success evidence, and stop or
  handoff condition. Separate authenticated human, tenant, and target-resource
  identity from the worker's operational role and presentation persona.
  Derive authorization from the authenticated principal, scoped capability,
  and persisted target. Role, persona, model, provider, or chat title cannot
  change identity, tenant, destination, grant, capability, or system policy.
  Persist and audit those fields separately; never use persona as an
  authorization signal.
- Separate chat context from durable job state. Long-running work keeps a stable
  job ID, checkpoint, owner, lease/fencing or equivalent concurrency control,
  cancellation path, and bounded artifact/receipt so another approved executor
  can resume it without rereading or trusting an entire chat transcript.
- Validate tool arguments before dispatch and validate the resulting domain
  state after execution. A model response, tool call, queue record, UI state,
  or passing unit test alone does not prove the intended effect.
- Keep tools narrow, named by capability, and economical in their returned
  context. A fallback may use only the same or narrower grant; provider failure
  never authorizes privilege escalation.
- Delegate independent work only when the tracks have separate ownership and
  can proceed without editing shared state. Give each worker a bounded output,
  checkout/branch, input SHA, and verification contract; the integrator checks
  overlap and validates the combined result. Avoid parallel agents when their
  coordination or token cost exceeds the time saved.
- For agentic behavior, define repeatable task cases and graders for intent
  fulfillment, protected invariants, correct tool/effect sequence, and final
  state. Track regressions, latency, resource use, and cost where they affect
  product behavior. Calibrate model-based graders against observable outcomes.
- When integrating a project, trace actual ingress → identity and authorization
  → dispatch → durable state → executor → external effect → verification →
  receipt/audit → recovery. Treat each other ingress path and runtime (Codex,
  Claude, self-chat, host, container, OS service) as a separate adoption claim
  until evidence shows it consumes the same contract.

For SOBER, the shared principles do not replace its canonical `CLAUDE.md`,
`ENVIRONMENT.md`, capability map, or domain roadmap. Use those project-owned
contracts for business rules and prove integration across each real transport
and executor.

## Delivery flow and runtime enforcement

- Put sequencing and authorization in the shared versioned executor/adapter, not only in AGENTS, skills, prompts, or model memory. Prompts explain the interface; typed operations, the canonical ledger, and host-side effect gates enforce it.
- The canonical project plan is the sole decision record and gate for a release. Keep it current as implementation, deployment, probes, and validation progress; do not create a parallel checklist or treat stale guidance as a competing gate.
- A release entrypoint must chain risk-specific preflight, exact-SHA deploy, production probes, and one post-deploy canonical suite run. Decide release success from that action-specific receipt while keeping unrelated inventory gaps visible as scoped coverage evidence in the same canonical plan. Do not rerun the full suite after each small commit.
- A merge or rebase that creates a new published SHA invalidates the prior SHA as proof for that commit. Advance the same canonical plan, refresh risk-specific preflight evidence for the new diff, and run deploy, probes, and one post-deploy suite for the new exact SHA before reporting delivery complete.
- Keep source release separate from dependency discovery. Resolving packages or workflow actions must be an explicit plan operation, never a hidden side effect of a routine release request.
- Prefer a reusable release command or adapter that safely chains these steps. Do not make the user repeat orchestration steps an adapter can reliably perform. Automatic merge/deploy may proceed only when the canonical plan's action-specific risk criteria pass and the adapter has a verified receipt; do not add a new owner confirmation between already authorized stages.
- Make deployment decisions from the action-specific deploy gate; unrelated inventory blockers must not block an otherwise authorized manual deploy. Unknown production risk, unproven recovery, or unavailable required probes remain blockers.
- Reconcile uncertain deployment effects from durable receipts before retrying; never replay an effect merely because a client timed out. Track active process handles and wait at sensible intervals rather than polling continuously.
- When harness guidance diverges from the canonical plan or the user's latest instruction, refactor its canonical source and align adapters/docs that carry stale behavior.

## Autonomous recovery

- An authorized mission must remain active across implementation, independent review, correction, validation, merge, deploy and post-deploy acceptance. This is the required lifecycle; installed executors need separate adoption evidence under “Behavior claims and implementation evidence”. Keep checkpoints and all attempts in the same canonical ledger/plan; do not create a second checklist or require the owner to reissue the same mission after an agent restart or provider quota event. A missing transition is an implementation gap to repair, and an external dependency blocks only the effects that require it.
- On a failed gate, persist the stage, exact SHA, bounded output and diagnostic; classify the blocker as automatically repairable, transient, or missing external authorization/proof. For a repairable failure, request independent review, apply a correction on the mission's existing branch/worktree, add a regression test, and re-evaluate the relevant gate. For a transient provider failure, preserve the checkpoint, try another executor already authorized for this mission, and resume with backoff.
- A repair may fix a faulty guard implementation only when a regression test proves the intended protected invariant remains enforced. Never remove authorization, isolation, tenant boundaries, evidence requirements, or uncertain-effect reconciliation to make a gate pass. Do not buy credits or broaden a grant.
- An external dependency pauses only effects that require the missing proof or grant. Keep the mission and monitor active; resume automatically when the dependency's verifiable resolution event arrives. Reconcile uncertain external effects before retrying.
- Persist standing owner authorization as a revocable grant in the canonical plan/ledger, scoped to the exact repository, environment, and effect classes (such as merge and production deploy). An explicit scoped owner instruction can supply the authorization basis; preserve it rather than requesting it again. A mission may chain only effects covered by that grant; do not invent unspecified scope from owner status, a broad goal or a repository flag. Record the grant reference with every effect receipt.
- GitHub Actions never decides merge, deploy, or release acceptance in this harness. The canonical plan and its exact-SHA receipts are the sole decision authority; Actions output may be diagnostic only.

## Learning from operational failures

Evolve the existing lifecycle and gates from demonstrated failures, rather than
accumulating project-specific warnings or claiming that instructions prevent all
future errors. Apply this loop to the affected capability; ordinary unrelated
tasks do not need a system-wide audit.

- Record the failure, affected source/configuration, operational consequence and
  falsifying check in the existing canonical mission/ledger. Separate a proposed
  cause from a reproduced failure. Keep private payloads and credentials out of
  lessons and reusable skills.
- Fix the responsible executable boundary in the core or its project adapter.
  A skill explains that contract; it does not enforce it. Reuse the existing
  ownership, checkpoint, effect-reconciliation and scratch mechanisms before
  adding another registry, runner, timer or cleanup path.
- A required effect that failed or remains uncertain cannot produce a completed
  receipt. Cover partial outcomes, retries after reconciliation, invalid versus
  absent input, no-change executions and exact source/artifact identity when
  those cases apply. A regression must reject the broken state and accept the
  correction without weakening grants, isolation or proof requirements.
- For concurrent or scheduled workflows, check every real entrypoint, including
  manual commands and background jobs, against the same writer/resource
  contract. Cleanup follows verified ownership and leases; age, provider exit or
  lack of a grep match does not authorize deleting work or stopping a service.
- Reuse unchanged evidence and measure idle work, repeated transfers, polling,
  process lifetime and resource cost before optimizing. Retain recovery paths
  with real consumers; classify unproven abandonment instead of removing it.
- Close a lesson only after the relevant host, executor and container/runtime
  consume the corrected revision and the observable failure case is prevented.
  Record adoption gaps explicitly. Do not auto-edit policy from an unreviewed
  agent summary, silently roll out to collaborators, or create a parallel memory
  file for each provider.

### Owner corrections and repeated instructions

- Treat the owner's latest explicit correction as the current requirement. Do
  not ask them to repeat scope, naming, ordering, or workflow constraints that
  are already present in the active conversation or canonical plan.
- When a correction changes a durable decision, update the existing mission
  plan/ledger in the same work session and carry it through the remaining work.
  When it exposes a reusable agent behavior, update the canonical skill or
  shared policy source that governs that behavior; do not stop at acknowledging
  the correction or create a parallel memory/diary.
- Convert the correction into a short operational rule and an observable
  acceptance condition. Preserve earlier constraints that remain compatible,
  and trace affected adapters/skills to their real consumers before claiming
  the correction is adopted.
- Keep the lesson free of private conversation, audio, credentials, and
  project-specific details that are not needed to reuse the behavior. A direct
  owner correction is reviewed input; an agent-generated summary is not
  authorization to rewrite policy.
- If the right canonical source or scope is unclear, inspect the existing plan,
  skill, code, and consumers first. Ask only about the remaining material
  ambiguity, while continuing independent work.

## Before changing a repo

1. Read the user's global `~/.codex/AGENTS.md`, the project's `AGENTS.md`/`CLAUDE.md`, and `Lucasdoreac/personal-dev-harness`, the canonical source of shared rules, this skill and its installer. `Lucasdoreac/dev-local` remains a LabTech-specific adapter, not a second global source. Core manifest/pin, project-local policy snapshot and Codex/Claude entrypoint bootstrap are implemented; the Antigravity global rules/skills/hooks adapter is implemented by the same sync installer. The shared scratch collector and Ubuntu/macOS service adapters are implemented in this rollout; verify their installation on each host and project-specific runtime/container consumption before claiming adoption. Installed host links do not prove universal adoption.
2. Identify repo owner, remote/default branch, active PRs/branches/worktrees, local changes, CI/runtime, and which agents/tools actually execute. Distinguish instructions from enforceable hooks, wrappers, OS services, CI, and remote policy.
3. Prefer one versioned core, a small project manifest/adapter, and a bootstrap/doctor command. Do not copy policy implementations into each repo or silently change remotes, default branches, org settings, or collaborator workflows.

## Lifecycle and cleanup

- Cleanup at normal shutdown uses `update_vanguard.scratch.managed_scratch` for agent, test, and provider work. It removes its own marked directory on normal exit.
- Crash recovery uses the same collector through systemd on Ubuntu and launchd on macOS. Install or repair these user services through `scripts/sync.py --install`; verify with `scripts/sync.py --check`.
- The collector only removes direct children in the dedicated per-user scratch root when the ownership marker is valid, age exceeds the threshold, the lease is unlocked, and the tree has no `.git` metadata. It preserves symlinks, unknown directories, worktrees, Git changes, arbitrary `/tmp` content, caches, model downloads, Docker volumes, databases, and backups.
- Mission worktrees are collected only by `harness-worktree-gc` (`update_vanguard.worktree_gc`): dry-run by default, `--apply` explicit. A linked, unlocked worktree is eligible only when its ledger claim is released (or it never had one), its branch is merged into the remote base (ancestor or same content), its tree is clean except an untracked `.venv`, no commit lies outside every remote ref, and no live process has its cwd inside it. It archives a bundle, diffs, HEAD and status under `~/dev/worktrees/.archive/` before `git worktree remove` (never `--force`) and deletes the local branch only when merged. The ledger is read read-only and never migrated.
- Revert-check normal exit, crash/stale candidate, active lease, young candidate, symlink/path escape, wrong owner, malformed marker, unknown directory, and a managed-looking tree containing Git metadata. If ownership or activity cannot be proven, report and leave the item untouched.

## Adoption and proof

- New repos should inherit the harness from the personal template/bootstrap at creation, with a project-specific manifest and pinned harness version. Bootstrap creates local Git; when the owner explicitly supplies an `OWNER/NAME` target, it can create/reconcile a private GitHub repo and set `origin` without pushing. Never derive a customer or collaborator destination from the owner portfolio. Existing repos are migrated in small batches after authority and compatibility checks; archived and third-party repos are classified, not mass-mutated.
- For each adoption, prove discovery and enforcement through the actual Codex, Claude, or Antigravity entry points in scope, a host run, and Docker/CI where the project requires it. For Antigravity, global rules are discovered from `~/.gemini/AGENTS.md`, `~/.gemini/GEMINI.md`, or `~/.gemini/config/{AGENTS.md,GEMINI.md}`; shared App/CLI skills belong under `~/.gemini/config/skills/`, and global hooks under `~/.gemini/config/hooks.json`. Verify loaded hooks in `/hooks` (CLI) or Customizations (App/IDE). Preserve unrelated Gemini customizations; a symlink, settings file, or passing isolated test alone does not prove runtime adoption.
- Track the rollout in the existing canonical plan/goal system. Record phases and dependencies once; do not create a duplicate memory file. Do not mark a phase complete from documentation or unit tests alone.
- Do not change organization-wide settings, install persistent OS services, or delete existing state without scoped authorization. Push, PR, merge, and deploy are allowed only when the canonical grant covers the repository, environment, and action. Preserve local work and do not change collaborators' ownership or environment.

## Work distribution

For routing work by cost tier (local on-device, cheap, capable, judge), escalation between tiers, local Apple Foundation Models, or recovering another provider's interrupted state, use the sibling skill `tiered-delegation`. It applies the agent and delivery rules above; it does not replace them.
