# skills

One directory per [Agent Skill](https://agentskills.io): a `SKILL.md` carrying YAML frontmatter
(`name`, `description`) and the skill body, plus its own `scripts/` where the skill ships
executable helpers.

```
skills/
  <skill-name>/
    SKILL.md
    scripts/
```

The `description` is what a client matches a task against, so it states both what the skill
produces and the situations that should trigger it — including phrasings a user would actually
type rather than the skill's own name.

A skill here must be portable: no reference to a specific repository, spec file, product, or
directory outside its own folder. Name an artifact by the role it plays ("the project's
requirements document") rather than by its path.
