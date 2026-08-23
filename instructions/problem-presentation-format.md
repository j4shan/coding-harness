# Problem presentation format

**Objective.** Report every problem, defect and open decision in one fixed structure, so the
reader can tell at a glance what still needs their attention, how bad it is, and which part of the
system is at risk. Number every finding so later messages can cite it.

**Your tasks.** Decide whether this format applies, then number each finding and compose one
entry per finding using the fields and layout below.

## 1. Decide whether to use this format

Use it when any of these hold:

- the user asks for an explanation of a problem;
- you are composing defects found, problem descriptions, or open decisions into a review-request
  response or a plan-execution summary;
- you are presenting an open question, an issue resolved without asking, or a decision taken
  without asking.

Do not use it when the user asks for a simple or short explanation.

## 2. Compose the entry

Write one entry per finding. Give every entry a unique ID `P<n>`. Number from `P1` with no
gaps and no reuse. When this message adds findings to a list already numbered in the
conversation, continue from the next unused n. Cite a finding by its ID, never by order or
paraphrase.

Do not assume the reader's knowledge in code. Illustrate the point using product or business
concepts, requirements, constraints and documented terms. When you need a code reference, place
the citation at the end of the field in this format: `[<relative_file_path>/<file_name>: <line_#>]`.

Render the list in this exact shape. Write a markdown thematic break (`---` on its own line)
before the first entry, between every pair of entries, and after the last entry. Never omit a
break because there is only one finding. Never write two breaks in a row.

```
---

**P1**

**Category:** …
**Scope:** …
**Severity:** …
**Components:** …
**Problem Description:** …
**Cause:** …
**Evidence:** …
**Action:** …
**Status:** …

---

**P2**

…

---
```

Use **Proposed Action** in place of **Action** on open-question entries. Omit **Evidence** and
**Action** only when the field table says they do not apply.

Fill these fields.

| Field | What goes in it |
| --- | --- |
| **ID** | `P<n>` — unique in this conversation; the entry heading |
| **Category** | one or more labels from the category table below |
| **Scope** | one or more labels from the scope table below |
| **Severity** | `blocking` · `degrading` · `cosmetic` |
| **Components** | the layer — `front end` · `back end` · `data model` · `API / CLI` · `build pipeline` — then the area inside it (for a front-end concern, which screen or section), and the file |
| **Problem Description** | three parts, in order: (1) `When: always` or `When: <condition>`; (2) a one-sentence problem summary; (3) one concise paragraph of detail. No cause here |
| **Cause** | the mechanism, the wrong assumption, or the missing rule. **Prefer concision:** one sentence unless a second is load-bearing |
| **Evidence** | problem and defect entries only. Required whenever the entry asserts a number |
| **Action** | problem and defect entries only — what was done, or what is proposed |
| **Proposed Action** | open-question entries only — the options, and a recommendation among them |
| **Status** | `resolved` · `resolved, enforced forward` · `unresolved — decision needed` · `accepted — recorded in <id>` · `out of scope` |

| Scope | Covers |
| --- | --- |
| `production` | code and assets that ship and run as the product |
| `test` | code that verifies the product, and the fixtures it runs on |
| `development tooling` | tools and config that generate or shape source and tests — codegen, scaffolding, linter and formatter config, developer utility scripts, and instructions or skills written for AI coding agents |
| `build & deploy` | build, packaging, dependency, CI/CD and deployment config — the pipeline that transforms and ships what was authored |
| `project documentation` | PRD, design specs, execution plans, defect reports, and reference material written for people |

| Category | Covers |
| --- | --- |
| `scientific theory` | the analytical model, the objective or success measure it is judged by, and the semantics of a metric — including one whose definition has stopped matching what it measures |
| `product design` | what the product should do or present, and how a reader experiences it |
| `specification defect` | a requirement that is wrong, ambiguous, unimplementable, or contradicts another |
| `coding implementation` | the code does not do what the specification says, or does it in a way that will not hold |
| `security` | anything that widens what untrusted input can reach. Never folded into `coding implementation` |
| `architecture / seam` | a contract or boundary between modules. The action is accept-or-redesign, not a local fix |
| `process / planning` | the plan or task graph is wrong — work specified but unscheduled, or scheduled but unspecified |

Two rules:

- A pending decision never sits inside an entry about something already fixed. It stands alone.
- A finding that contradicts an earlier "done" says so in **Action**, and corrects the earlier
  claim in the same message. Cite the earlier finding by ID when it has one.
