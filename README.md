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

## Install

`install.sh` copies everything here into the locations each client reads at **user scope**, so
every project on the machine picks it up without a per-project copy. macOS only.

```bash
./install.sh            # both clients (same as --all)
./install.sh --claude   # Claude Code only
./install.sh --cursor   # Cursor only
```

| | Skills | Instructions |
| --- | --- | --- |
| **Claude Code** | `~/.claude/skills/<name>/` | `~/.claude/rules/<name>.md` |
| **Cursor** | `~/.cursor/skills/<name>/` | `~/.cursor/rules/<name>.mdc` |

Instructions are given to each client in the shape it loads: verbatim for Claude Code, which reads
every `.md` in `~/.claude/rules/` at session start, and wrapped in `description` / `alwaysApply`
frontmatter for Cursor. The `README.md` in each source directory documents that directory and is
never installed.

Where a destination already exists the script lists every collision and asks once, defaulting to
overwrite; answering `n` skips all existing items and installs the rest. Skill folders are replaced
whole, so a file deleted here does not survive in an install.

Restart the client afterwards — skills and rules are read at session start.

> Cursor's global rules directory is community-documented rather than official; Cursor's own docs
> describe User Rules only through Customize → Rules. Confirm the rules appear there after
> installing.

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
