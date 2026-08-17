---
name: execution-planning
description: Use whenever a plan is being produced — Plan mode is active, or the user asks to plan a project, create an execution plan, break an objective into tasks, or build a task DAG. Produces a topologically ordered task table carrying every dependency edge, a per-task executor and model assignment, and a success criterion per task that governs execution. Reach for this whenever multi-step work needs scoping, sequencing, breaking down, or delegating, even if the user never says "execution plan" or "DAG".
---

# Execution Planning

Turn an objective into an **execution plan**: what the tasks are, what depends on
what, who runs each one, on which model, and how completion is tracked.

## Integration rule

This skill complements the default planning procedure rather than replacing it.
The default procedure still owns **investigation and technical approach** — read
the code, find the real constraints, decide *how* the work should be done.

This skill owns **execution structure**: decomposition, the dependency DAG,
delegation, model routing, and goal tracking. Where any other planning guidance
overlaps or contradicts this skill on those concerns — an unordered task list, no
executor assignment, hand-drawn ordering — **this skill wins**.

Plan on **Opus at high effort**. If the session is on a different model, say so
and offer to switch before producing the plan; a plan written cheaply is paid for
many times over during execution.

## Procedure

### 1. Decompose

Break the objective into discrete tasks. Let the objective decide how many —
enough that each task is independently checkable, not so many that the table
stops being readable. Give each a stable kebab-case id and a one-line success
criterion stating what "done" means.

Split rules:

- **Project metadata is its own task.** Build config, dependency manifests, and
  CI/CD changes never ride along with source or test edits — they have different
  reviewers, different failure modes, and different blast radius. One task for
  metadata, separate tasks for source and tests.
- **A spec sync is always a top-level task**, depending on every task that could add,
  remove, or alter a requirement, so the plan ends with the project's product requirement
  and design spec documents matching what was built.
- Prefer tasks that can be verified without running the tasks downstream of them.

### 2. Build the DAG

Capture only **immediate** dependencies as pairs — `A > B` means A must finish
before B starts. Don't write transitive edges (if `A > B` and `B > C`, never add
`A > C`), and don't work out the ordering yourself.

Run the tool; its output is authoritative for numbering and ordering. It lives at
`scripts/task_dag.py` inside this skill's directory — pass that full path, since
the shell starts in the project root:

```bash
python3 .agents/skills/execution-planning/scripts/task_dag.py \
  "audit > design" "survey > design" "design > build" --task docs
```

It numbers tasks `T1..Tn` in topological order and emits the task table plus an
echo of the edges you gave it — that pairing is for **iterating on the graph while
planning**. `--format table|pairs|json` selects one; a JSON payload
(`{"tasks": [...], "edges": [[src, dst], ...]}`) can be piped on stdin.

The `T` prefix is load-bearing in a repo whose spec clauses are themselves dotted
numbers: it keeps `T12` from reading as requirement `12`.

On `error: cycle detected: ...` the decomposition is circular — fix the pairs and
re-run. Never hand-edit the tool's output.

### 3. Assign an executor

Every task gets exactly one: **main agent** or **subagent:\<type\>**.

Delegate to a subagent when:

- The task **accumulates long trial-and-error context** — web search, MCP code
  search (GitLab, Sourcegraph), log spelunking, reproducing a flaky failure.
  The subagent absorbs the dead ends and returns only the conclusion.
- The task is a **code review**. Always a subagent — a reviewer that also wrote
  the code reviews its own intentions.
- The task is independent, I/O-heavy, and maps cleanly to an available agent type.

Keep on the main agent: shared or global state, cross-task synthesis, final
decisions, and anything that must invoke `Skill` or spawn further agents
(subagents cannot reliably spawn subagents).

**Every task must appear as a row in the Task Assignment table with both an
executor and a model filled in — no omissions, no blank cells.**

### 4. Route models

Every task carries a model floor of at least **(Sonnet, effort high)** or
**(Opus, effort medium)**. Never route a task to Haiku or Fable unless the user
explicitly asks for it. Record the choice per task — when delegating, pass
`model: opus` or `model: sonnet` to the `Agent` call; effort comes from the agent
definition, so note it in the plan when it needs to be raised.

### 5. Emit the plan

Generate the document shell from the same tool — it fills in every derived cell
(ids, edges, table rows) so nothing is transcribed by hand:

```bash
python3 .agents/skills/execution-planning/scripts/task_dag.py \
  --format scaffold --title "<objective>" "audit > design" ...
```

Then fill the placeholders and write the result to **whatever plan file the host
already has open** — Plan mode provisions one and names it, and that is the file
the user will be shown. This skill has no opinion about the path or the filename;
if no plan file has been established and the caller named no destination, ask
rather than inventing one.

## Plan document contract

These headings are the shared vocabulary between the agent that writes the plan
and the agent that later executes it, so keep them verbatim.

- `## Problem Statement` — opens the plan: what is broken or missing today and why
  it is worth changing. Follow it with a **Goals** bullet list (mandatory) and a
  **Non-goals** bullet list (only when the user supplied non-goals — never invent
  them; omit the block otherwise).
- `## Task DAG` — the tool-generated table, unedited except for filling in each
  success criterion:
  `| Task # | Task | Depends on | Unblocks | Success criterion | Status |`,
  every row starting at `pending` (`pending | in_progress | done | failed`).
  It is the whole graph — both directions of every edge are in it, so nothing is
  gained by drawing one.
- `## Task Assignment` — `| Task # | Executor | Model | Rationale |`, joined to the
  table above by `Task #`, where Executor is `main-agent` or `subagent:<type>`.
- `## Execution Protocol` — the two things that are fixed are the dependency edges
  and the per-task executor and model. **Pacing is the executor's call, not the
  plan's.** Start any task whose `Depends on` entries are all `done`; when several
  come ready at once, launch the `subagent:` ones in a single message with multiple
  `Agent` calls so they genuinely run in parallel. Never make a task wait on
  something absent from its `Depends on` cell — staged rounds that wait for a whole
  batch to finish idle work that was ready to go. On a failure, everything
  reachable downstream is blocked and the rest of the graph continues; record here
  anything waived, and why.
