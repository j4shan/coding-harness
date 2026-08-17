# Agent Skills

Project skills are [Agent Skills](https://agentskills.io) folders under **`.agents/skills/`** — a
`SKILL.md` plus its own `scripts/`. That open convention is the only location a project should
use: no skill is duplicated or symlinked into a vendor-specific directory, so a skill added there
is available to every client that follows the convention.

Select a skill by matching the task against its `SKILL.md` description. Paths inside a skill are
written from the repository root — `.agents/skills/<name>/scripts/…` — because that is where the
shell starts.
