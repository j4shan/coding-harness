# coding-harness

Reusable configuration for AI coding agents — the parts that are worth carrying from one project
to the next, kept in one place instead of being re-derived or copy-pasted per repository.

## What lives here

| Directory | Contents |
| --- | --- |
| [`skills/`](skills/) | [Agent Skills](https://agentskills.io) folders — one directory per skill, each a `SKILL.md` plus its own `scripts/` |
| [`instructions/`](instructions/) | Instruction documents written to be read by an agent — working conventions, review formats, authoring rules |

MCP server definitions are also in scope for this repository; no directory has been designated for
them yet.

## Using a skill in another project

A skill here is portable by construction: it names no repository, no file path outside its own
folder, and no vendor-specific directory. To use one, copy or symlink its folder into the target
project's `.agents/skills/`, which is the cross-client convention that Codex and Cursor discover
natively.

Paths written inside a skill are relative to the *consuming* project's root — `.agents/skills/<name>/scripts/…` —
because that is where the shell starts.

## Contributing back

Anything added here must be **general**: it must make sense in a repository that knows nothing
about the project it came from. A skill or instruction that names a specific spec file, product,
or directory layout belongs in that project, not in this one. Where a rule is genuinely useful but
carries a project-specific detail, state the rule by the role the artifact plays rather than by its
path.
