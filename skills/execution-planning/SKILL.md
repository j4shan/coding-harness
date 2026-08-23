---
name: execution-planning
description: Use whenever a plan is being produced — Plan mode is active, or the user asks to plan a project, create an execution plan, break an objective into tasks, or build a task DAG. Produces serial functional goals, a category-sliced task DAG with one agent per file category, a prose body and success criterion per task, and the protocol that governs execution. Reach for this whenever multi-step work needs scoping, sequencing, breaking down, or delegating, even if the user never says "execution plan" or "DAG".
---

# Execution Planning

Turn an objective into an **execution plan**: serial functional goals, category
slices, who owns each file category, on which model, how each slice is done, and
how completion is tracked.

## Integration rule

This skill complements the default planning procedure rather than replacing it.
The default procedure still owns **investigation** — read the code, find the
real constraints, decide *how* the work should be done. Write that *how* into
each slice body (files, consumes, produces, verify). The later executor follows
the body; it does not invent a second approach.

This skill owns **execution structure**: decomposition, the dependency DAG,
category pinning, model routing, and goal tracking. Where any other planning
guidance overlaps or contradicts this skill on those concerns — an unordered
task list, no category assignment, hand-drawn ordering, or extra waves beyond
serial goals — **this skill wins**.

Plan on **Grok 4.6 at high effort**. If the session is on a different model, say
so and offer to switch before producing the plan; a plan written cheaply is paid
for many times over during execution. Plan on Opus or Gemini Pro only when the
user named that preference.

## Procedure

### 1. Decompose

Name **functional goals** in delivery order. Those rows are the plan's Goals
table. Goals are serial: goal 2 does not start until every slice of goal 1 is
`done` or `waived`. That serial goal is the only wave; do not invent others.

For each goal, add at least one **slice** and at most one slice per **file
category** that goal actually touches. A slice is the executable task: a stable
kebab-case id, a one-line **observable** success criterion (what an observer
would check, not "implement X"), and a prose body.

Every project file belongs to exactly one category:

- `code` — application source and the tests that prove that slice
- `config` — build, CI/CD, dependency manifests, tooling config
- `docs` — product requirements, implementation guidelines, human docs
- `assets` — static resources that are none of the above

Tie-break: `package.json` and CI → `config`; test files and test fixtures →
`code`; README / product requirements / implementation guidelines → `docs`.

Split rules:

- A slice edits files in exactly one category. Every path in its body belongs
  to that category.
- Keep the spec sync out of the other slices. When section 2 says the plan needs
  one, it is its own `docs` slice, never an edit riding along with `code`,
  `config`, or `assets` work.
- Prefer slices that can be verified without running slices downstream of them.
  A `code` slice is independently checkable only if its success criterion can be
  proven with artifacts in that slice, including tests written and run there. Do
  not split "implement" from "test" as sibling slices under one goal. Extra
  coverage may be a later `code` slice (same agent, typically a later goal).
- A wait on a person or an external system is a slice with a success criterion,
  not a note outside the DAG.

### 2. Decide whether the plan needs a spec sync

Add a **spec sync** slice only when the work changes what the spec asserts.
Judge by what changes, never by how large the diff is.

Add it when any slice will:

- add, remove, or alter a product requirement or a user-visible behavior;
- change an interface, contract, or data model the spec describes;
- adopt, change, or retire an implementation guideline the user supplied;
- make a clause the spec still asserts false.

Never add it when every spec clause stays true after the work — a coding-style
refactor, a rename that moves no contract, test-only work, a dependency bump, a
performance change at unchanged behavior. Say in the plan that no spec sync is
needed and why; never drop the question silently.

When the plan needs one:

- Make it a `docs` slice in a final goal, depending on every slice that could
  add, remove, or alter a requirement, so the plan ends with the spec matching
  what was built. Serial goals already wait on the previous goal; still name
  the spec-sync slice and list its clauses.
- Update exactly two things: the **high-level product requirements**, and the
  **user-supplied implementation guidelines**. Never push task-level detail,
  code structure, or anything a reader could derive from the source into the
  spec.
- List every clause the sync will touch in the plan's `## Spec Sync` section,
  so the user reviews the spec change before any slice runs. Every `Driven by`
  cell names a `Task #` that exists on the DAG.

### 3. Build the DAG

Capture only **immediate intra-goal** dependencies as pairs — `A > B` means A
must finish before B starts. Don't write transitive edges (if `A > B` and
`B > C`, never add `A > C`). Don't write cross-goal pairs; goals are serial and
the tool inserts the cut. Don't work out the numbering yourself.

Run the tool; its output is authoritative for numbering, ordering, and
goal-cut edges. It lives at `scripts/task_dag.py` inside this skill's
directory — pass that full path, since the shell starts in the project root:

```bash
python3 .agents/skills/execution-planning/scripts/task_dag.py \
  --goal-order add-cache,ship \
  --slice add-cache:code:implement \
  --slice add-cache:config:wire-ci \
  --slice ship:docs:spec-sync \
  "implement > wire-ci"
```

A JSON payload is the full form and can be piped on stdin:

```json
{
  "goals": ["add-cache", "ship"],
  "tasks": [
    {"id": "implement", "goal": "add-cache", "category": "code"},
    {"id": "wire-ci", "goal": "add-cache", "category": "config"},
    {"id": "spec-sync", "goal": "ship", "category": "docs"}
  ],
  "edges": [["implement", "wire-ci"]]
}
```

The tool numbers slices `T1..Tn` in topological order, fills the Goals `Tasks`
column, and inserts a goal-cut from every sink of goal *i* to every source of
goal *i+1*. `--format table|pairs|json` selects one. That pairing is for
**iterating on the graph while planning**.

The `T` prefix is load-bearing in a repo whose spec clauses are themselves
dotted numbers: it keeps `T12` from reading as requirement `12`.

On `error: cycle detected: ...` the decomposition is circular — fix the pairs
and re-run. On an empty goal, a second slice in the same goal and category, or
a cross-goal pair, fix the input and re-run. Never hand-edit the tool's output.

### 4. Pin one agent per category

Each file category used in the plan gets exactly one executor for the whole
plan: **main-agent** or **subagent:\<type\>**. That agent is the only writer in
that category. Never assign a second agent to a category. Copy the same
executor onto every slice in that category.

Choose the agent, then freeze it:

Delegate to a subagent when:

- The work **accumulates long trial-and-error context** — web search, MCP code
  search (GitLab, Sourcegraph), log spelunking, reproducing a flaky failure.
  The subagent absorbs the dead ends and returns only the conclusion.
- The work is independent, I/O-heavy, and maps cleanly to an available agent
  type.

Keep on the main agent: shared or global state, cross-goal synthesis, final
decisions, and anything that must invoke `Skill` or spawn further agents
(subagents cannot reliably spawn subagents).

When the executor is a subagent, pick `subagent:<type>` from the types this
session lists. Never invent a type. Never pass a separate `model:` argument —
the type already pins the model and the effort. Pass that slice's DAG row, its
body, its success criterion, and the Category Assignment row. The subagent
returns `done` or `failed` and whether the criterion holds.

For a hard slice, assign `cursor-grok-4.6-high`, `gpt-5.6-sol-medium`, or
`kimi-k3-high`. For an ordinary slice, assign `cursor-grok-4.6-medium` or
`gemini-3.7-flash-high`. If no listed type matches the chosen route, keep that
category on `main-agent`.

Never assign `claude-opus-5-high` or `gemini-3.1-pro` unless the user named
that model.

**Every category used must appear as a row in Category Assignment. Every slice
must appear as a row in Task Assignment with a model filled in — no omissions,
no blank cells.**

Do not add a required review stage. A review-like slice is allowed only as an
ordinary category slice and follows the same assignment rules.

### 5. Route models

Every slice carries a model floor of at least **(Grok, effort medium)** or
**(Gemini Flash, effort high)**. Prefer **(Grok, effort high)**, **(GPT-Sol,
effort medium)**, or **(Kimi K3, effort high)** for a hard slice.

Never route a slice to Opus or Gemini Pro unless the user explicitly named
that preference.

When the executor is a model-pinned subagent, copy that pin into the Task
Assignment Model cell. When the executor is `main-agent`, fill the cell from
the floor and preference above. Record the choice per slice.

### 6. Emit the plan

Generate the document shell from the same tool — it fills in every derived
cell (ids, edges, table rows, goal-cut, task-body stubs) so nothing is
transcribed by hand:

```bash
python3 .agents/skills/execution-planning/scripts/task_dag.py \
  --format scaffold --title "<objective>" \
  --goal-order add-cache,ship \
  --slice add-cache:code:implement \
  --slice add-cache:config:wire-ci \
  --slice ship:docs:spec-sync \
  "implement > wire-ci"
```

Fill every placeholder in the tables and in each slice body. Then check:

- every Goals `Tasks` cell lists at least one `Task #`;
- every slice has a filled body;
- every Spec Sync `Driven by` names a `Task #` on the DAG, or the section is
  the one line saying no clause changes and why;
- no leftover `<...>` placeholders remain;
- each success criterion is observable.

Write the result to **whatever plan file the host already has open** — Plan
mode provisions one and names it, and that is the file the user will be shown.
This skill has no opinion about the path or the filename; if no plan file has
been established and the caller named no destination, ask rather than
inventing one.

Ask `Confirm plan? [1. Yes / 2. No]` and wait. On `2`, revise the plan; do not
start any slice. On `1`, stop unless the user also asked to execute. If they
did, follow Execution Protocol (spec-sync confirm still before any slice).

## Plan document contract

These headings are the shared vocabulary between the agent that writes the plan
and the agent that later executes it, so keep them verbatim.

- `## Problem Statement` — opens the plan: what is broken or missing today and
  why it is worth changing. Follow it with the **Goals** table (mandatory), a
  **Non-goals** bullet list (only when the user supplied non-goals — never
  invent them; omit the block otherwise), and a **Constraints** bullet list
  (only when the spec or user named them — never invent them; omit otherwise).
- **Goals** — `| Goal | Tasks |`, rows in delivery order. `Tasks` lists the
  `Task #` values whose DAG `Goal` cell matches. A blank `Tasks` cell is
  invalid. Goal ids in this table and in the DAG `Goal` column are the same
  strings, in the same order.
- `## Task DAG` — the tool-generated table, unedited except for filling in each
  success criterion:
  `| Task # | Goal | Category | Task | Depends on | Unblocks | Success criterion | Status |`,
  every row starting at `pending`. Status is only
  `pending | in_progress | done | failed | blocked | waived`.
  Use `blocked` when a slice cannot run because a prerequisite or an earlier
  goal `failed`. Use `waived` for an intentional skip (spec-sync `2`), not for
  a run that attempted and failed. It is the whole graph — both directions of
  every edge are in it, including tool-inserted goal-cuts, so nothing is gained
  by drawing one.
- `## Category Assignment` — `| Category | Executor | Rationale |`, one row per
  category used, executor unique for the whole plan
  (`main-agent` or `subagent:<type>`).
- `## Task Assignment` — `| Task # | Model | Rationale |`, joined to the DAG by
  `Task #`. No Executor column; executor comes from the slice's category.
- `## Tasks` — after Task Assignment and before Spec Sync. One
  `### {Task #} {id}` subsection per slice, in `T` order. Each body has exactly:
  - **Files** — create/modify paths; every path is in this slice's category
  - **Consumes** — what this slice uses from earlier slices (names and types),
    or `—`
  - **Produces** — what later slices rely on, or `—`
  - **Verify** — the command or check that proves the success criterion
  Do not add TDD step lists or pasted implementation code unless the user asked.
- `## Spec Sync` — one row per spec clause the sync will touch:
  `| Clause | Document | Change | Driven by |`, where Document is the high-level
  product requirements or the user-supplied implementation guidelines, Change
  is `add | amend | remove`, and Driven by names a `Task #` present on the DAG.
  Name the clause, never a whole document. Where the plan carries no spec sync
  slice, keep the heading and write the one line saying no clause changes and
  why — no empty Driven-by rows.
- `## Execution Protocol` — do not start any slice until `Confirm plan?
  [1. Yes / 2. No]` has been answered `1`. On `2`, revise; start no slice. If
  this plan has a spec sync slice, show the `## Spec Sync` table and ask
  `Confirm spec update? [1. Yes / 2. No]` before any slice, and wait. On `2`,
  mark that slice `waived`, record a waiver line, and run the rest of the
  graph.

  Goals are serial; category slices are the only parallel dimension. Start a
  slice only when every `Depends on` entry is `done` or `waived` **and** every
  slice of every earlier goal is `done` or `waived` (never `failed` or
  `blocked`). When several slices of the current goal are ready, launch the
  `subagent:` ones in one message with multiple `Agent` calls (at most one per
  category). Mark the row `in_progress`, then `done` or `failed`. Intra-goal
  edges still bind: not every slice of a goal is parallel.

  On `failed`, mark every reachable dependent `blocked`. Other category slices
  of the same goal may continue. Later goals stay `blocked`. On a wrong or
  missing edge, stop, fix the pairs, re-run the tool, and replace the tables.
  Never patch numbering by hand.

  End with a **Waivers** list: one line per item (what was dropped and why).
  Omit the heading until a waiver exists.
