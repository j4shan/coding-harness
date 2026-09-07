# Project metadata guideline

**Objective.** Keep project-owned documents and authored assets in a fixed tree so later
sessions find requirements, contracts, plans, and exhibits in one place.

**Your tasks.** Maintain the product spec, place project metadata, and place authored
resources. Each section states when it applies.

## 1. Capture a requirement

When the user states a product requirement — what the product is, what it must do, how it
must behave, or how it must look and feel — write it into the PRD for the matching
top-level component. Create that file if it does not exist — this is your responsibility,
not a precondition to wait on.

When the prompt states no new product requirement, leave the product spec unchanged.

The word **spec** means these PRD files and nothing else.

Never write a decision the system resolved on its own and the user did not confirm. Typical
examples: UI widget theme, colour code, size.

Never write coding implementation guidelines, tools and dependencies, or build processes
unless the user explicitly requested them.

## 2. Keep one PRD per top-level component

Put each top-level system component in its own file under `project_metadata/product_spec/`,
relative to the project root.

## 3. Identify every clause

Give every clause a hierarchical dotted id — `1.2.3` — unique across the product spec. The
spec is a snapshot of current requirements, not a version history. Delete a superseded
clause. Never strike it through, annotate it, or renumber remaining ids.

## 4. Review the spec when changing code

Read the product spec before you change code. Where the spec and the code disagree, say
which is the defect and fix that one. Never silently reword a clause to match the code.

## 5. Retire a requirement

When the user retires a requirement, delete the clause.

## 6. Place project metadata

Keep project-owned documents under `project_metadata/`, relative to the project root.

- Put product requirements in `project_metadata/product_spec/`. Follow the product-spec
  commands above.
- Put project-owned writing and generation contracts in `project_metadata/instructions/`.
- Put transient execution plans in `project_metadata/plans/`. Never version them.

## 7. Place authored resources

Keep authored exhibit and fixture assets under `resources/`, relative to the project root.
Never put temporary or git-ignored resources there.

- Put authored HTML, canvases, and formal documents in `resources/html/`.
- Put figures in `resources/img/`.
- Put figure prompts in `resources/img_prompt/`.
- Put authored scenario and fixture data in `resources/data/`. Do not put runtime-generated
  data there.
