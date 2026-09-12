---
name: execution-planning
description: Use whenever a plan is being produced. Plan mode is active, or the user asks to plan a project, create an execution plan, break an objective into tasks, or build a task DAG. Produces serial functional goals, a task DAG sliced by file category, one agent per category, a model and an observable success criterion per task, and a prose body saying how each task is done. Reach for this whenever multi-step work needs scoping, sequencing, breaking down, or delegating, even if the user never says "execution plan" or "DAG".
---

# Execution planning

**Objective.** Turn an objective into a written execution plan: serial functional goals, a task DAG
sliced by file category, one agent per category, a model per task, and a success criterion an
observer can check. The plan is static. It is written, reviewed, confirmed, then read by whoever
executes it, so it carries no status and no run state.

**Your tasks.** Decompose the objective, decide whether the spec changes, build the DAG with the
tool, pin one agent per category and route its model, then emit the plan and confirm it.

## How this fits other planning guidance

The default planning procedure owns investigation. Read the code, find the real constraints, decide
how the work should be done, and write that how into each task body. The executor follows the body
and does not invent a second approach.

This skill owns execution structure: decomposition, the dependency DAG, category pinning, model
routing, and the shape of the document. Where other guidance contradicts this skill on those
points, with an unordered task list, no category assignment, hand-drawn ordering, or extra waves
beyond serial goals, this skill wins.

Plan on Grok 4.6 at high effort. If the session is on a different model, say so and offer to switch
before producing the plan. Plan on Opus or Gemini Pro only when the user named that preference.

## 1. Decompose

Name the functional goals in delivery order. Those rows are the plan's Goals table. Goals are
serial: goal 2 does not start until every task of goal 1 has finished. That serial goal is the only
wave. Do not invent others.

Give each goal at least one task, and at most one task per file category that goal actually
touches. A task is the executable unit: a stable kebab-case id, a one-line success criterion an
observer could check rather than "implement X", and a prose body.

Every project file belongs to exactly one category:

- `code`, application source and the tests that prove that task
- `config`, build, CI/CD, dependency manifests, tooling config
- `docs`, product requirements, implementation guidelines, human docs
- `assets`, static resources that are none of the above

Tie-break: `package.json` and CI go to `config`. Test files and fixtures go to `code`. README,
product requirements, and implementation guidelines go to `docs`. Agent instruction documents,
skills, and subagent definitions go to `docs`; their helper scripts and the tests over them go to
`code`.

Split rules:

- A task edits files in exactly one category. Every path in its body belongs to that category.
- Keep the spec sync out of the other tasks. When section 2 says the plan needs one, it is its own
  `docs` task, never an edit riding along with `code`, `config`, or `assets` work.
- Prefer tasks verifiable without running anything downstream. A `code` task is independently
  checkable only if its success criterion can be proven with artifacts in that task, including
  tests written and run there. Do not split "implement" from "test" as sibling tasks under one
  goal. Extra coverage may be a later `code` task, same agent, usually a later goal.
- A wait on a person or an external system is a task with a success criterion, not a note outside
  the DAG.

## 2. Decide whether the plan needs a spec sync

Add a spec sync task only when the work changes what the spec asserts. Judge by what changes, never
by how large the diff is. Add it when any task will:

- add, remove, or alter a product requirement or a user-visible behavior;
- change an interface, contract, or data model the spec describes;
- adopt, change, or retire an implementation guideline the user supplied;
- make a clause the spec still asserts false.

Never add it when every spec clause stays true afterwards: a coding-style refactor, a rename that
moves no contract, test-only work, a dependency bump, a performance change at unchanged behavior.
Say in the plan that no spec sync is needed and why. Never drop the question silently.

When the plan needs one, make it a `docs` task in a final goal, depending on every task that could
add, remove, or alter a requirement, so the plan ends with the spec matching what was built. Update
exactly two things: the high-level product requirements, and the user-supplied implementation
guidelines. Never push task-level detail, code structure, or anything a reader could derive from
the source into the spec. List every clause the sync will touch in `## Spec Sync`, so the user
reviews the spec change before any task runs.

## 3. Build the DAG

Capture only immediate intra-goal dependencies as pairs. `A > B` means A must finish before B
starts. Do not write transitive edges: if `A > B` and `B > C`, never add `A > C`. Do not write
cross-goal pairs. Do not work out the numbering yourself.

Run the tool. Its output is authoritative for numbering, ordering, and goal-cut edges. It lives in
this skill's directory, so pass the full path, since the shell starts in the project root:

```bash
python3 .agents/skills/execution-planning/scripts/task_dag.py \
  --goal-order add-cache,ship \
  --task add-cache:code:implement \
  --task add-cache:config:wire-ci \
  --task ship:docs:spec-sync \
  "implement > wire-ci"
```

While iterating on the graph, `--format pairs` prints the edges alone.

On `error: cycle detected: ...` the decomposition is circular. Fix the pairs and re-run. On an empty
goal, a second task in the same goal and category, or a cross-goal pair, fix the input and re-run.
Never hand-edit the tool's output.

## 4. Pin one agent per category and route its model

Each file category used gets exactly one executor for the whole plan, either `main-agent` or
`subagent:<type>`. That agent is the only writer in that category. Never assign a second agent to a
category. Copy the same executor onto every task in that category.

Delegate to a subagent when either holds:

- The work accumulates long trial-and-error context, such as web search, MCP code search, log
  spelunking, or reproducing a flaky failure. The subagent absorbs the dead ends and returns the
  conclusion.
- The work is independent, I/O-heavy, and maps cleanly to an available agent type.

Keep on the main agent: shared or global state, cross-goal synthesis, final decisions, and anything
that must invoke `Skill` or spawn further agents, since subagents cannot reliably spawn subagents.

When the executor is a subagent, pick `subagent:<type>` from the types this session lists. Never
invent a type. Never pass a separate `model:` argument, because the type already pins the model and
the effort. Pass that task's DAG row, its body, its success criterion, and the Category Assignment
row.

Write a subagent type id in every Task Assignment `Model` cell, so one vocabulary covers the column.
For a hard task use `cursor-grok-4.6-high`, `gpt-5.6-sol-medium`, or `kimi-k3-high`. For an ordinary
task use `cursor-grok-4.6-medium` or `gemini-3.7-flash-high`. Where the executor is `main-agent`,
the cell names the model and effort the session should be running on, written with the same ids.
Never write `claude-opus-5-high` or `gemini-3.1-pro` unless the user named that model. Where no
listed type matches the chosen route, keep that category on `main-agent`.

Every category used must appear as a row in Category Assignment. Every task must appear as a row in
Task Assignment with a model filled in. No omissions, no blank cells.

Do not add a required review stage. A review-like task is allowed as an ordinary category task and
follows the same assignment rules.

## 5. Emit the plan

Generate the document shell from the same tool, which fills in every derived cell so nothing is
transcribed by hand. Use the section 3 command with `--format scaffold --title "<objective>"` added.

Fill every placeholder in the tables and in each task body, then run the checker and fix everything
it reports:

```bash
python3 .agents/skills/execution-planning/scripts/check_plan.py <plan file>
```

The checker reads the document only. Judge the two things it cannot: whether each success criterion
is observable, and whether the spec sync decision is right.

Write the result to whatever plan file the host already has open. Plan mode provisions one and names
it, and that is the file the user will be shown. This skill has no opinion about the path or the
filename. If no plan file has been established and the caller named no destination, ask rather than
inventing one.

Ask `Confirm plan? [1. Yes / 2. No]` and wait. On `2`, revise the plan and start no task. On `1`,
stop unless the user also asked to execute.

Where the plan carries a spec sync task, show the `## Spec Sync` table and ask `Confirm spec update?
[1. Yes / 2. No]` before any task starts, and wait. On `2`, drop the spec sync task, write one line
in the plan saying why, and re-run the tool so the numbering stays generated.

## Plan document contract

These headings are the shared vocabulary between the agent that writes the plan and the agent that
later executes it, so keep them verbatim.

- `## Problem Statement` opens the plan: what is broken or missing today and why it is worth
  changing. Follow it with the Goals table, which is mandatory, then a Non-goals list only when the
  user supplied non-goals, then a Constraints list only when the spec or user named them. Never
  invent either list. Omit the block instead.
- Goals is `| Goal | Tasks |` in delivery order. `Tasks` lists the `Task #` values whose DAG `Goal`
  cell matches, and a blank cell is invalid. Goal ids here and in the DAG `Goal` column are the same
  strings in the same order.
- `## Task DAG` is the tool-generated table, unedited except for filling in each success criterion:
  `| Task # | Goal | Category | Task | Depends on | Success criterion |`. Never draw a separate
  dependency diagram.
- `## Category Assignment` is `| Category | Executor | Rationale |`, one row per category used,
  executor unique for the whole plan.
- `## Task Assignment` is `| Task # | Model | Rationale |`, joined to the DAG by `Task #`. It has no
  Executor column, because the executor comes from the task's category.
- `## Tasks` comes after Task Assignment and before Spec Sync, with one `### {Task #} {id}`
  subsection per task in `T` order. Each body has exactly Files, the create and modify paths, every
  one in this task's category; Consumes, what this task uses from earlier tasks with names and
  types, or `—`; Produces, what later tasks rely on, or `—`; and Verify, the command or check that
  proves the success criterion. Do not add TDD step lists or pasted implementation code unless the
  user asked.
- `## Spec Sync` is one row per clause the sync will touch:
  `| Clause | Document | Change | Driven by |`, where Document is the high-level product
  requirements or the user-supplied implementation guidelines, Change is `add`, `amend`, or
  `remove`, and Driven by names a `Task #` present on the DAG. Name the clause, never a whole
  document. Where the plan carries no spec sync task, keep the heading and write the one line saying
  no clause changes and why, with no empty Driven by rows.
- `## Execution Guidelines` closes the plan. Goals are serial, and category tasks are the only
  parallel dimension. Within a goal, tasks with no edge between them run in parallel, at most one per
  category, and the ready `subagent:` ones launch in one message with multiple `Agent` calls.
  Intra-goal edges still bind, so not every task of a goal is parallel.
