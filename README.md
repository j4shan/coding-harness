# coding-harness

Reusable configuration for AI coding agents — the parts that are worth carrying from one project
to the next, kept in one place instead of being re-derived or copy-pasted per repository.

## What lives here

| Directory | Contents |
| --- | --- |
| [`skills/`](skills/) | [Agent Skills](https://agentskills.io) folders — one directory per skill |
| [`instructions/`](instructions/) | Instruction documents read by an agent — working conventions, review and reporting formats, authoring rules |

MCP server definitions are also in scope for this repository; no directory has been designated for
them yet.

[`AGENTS.md`](AGENTS.md) carries the rules for authoring what lives here, addressed to an agent
working in this repository. `CLAUDE.md` is a symlink to it, so Claude Code and Cursor read one file.

### Skills

One directory per skill: a `SKILL.md` carrying YAML frontmatter (`name`, `description`) and the
skill body, plus its own `scripts/` where the skill ships executable helpers.

```
skills/
  <skill-name>/
    SKILL.md
    scripts/
```

The `description` is what a client matches a task against, so it states both what the skill
produces and the situations that should trigger it — including phrasings a user would actually
type rather than the skill's own name.

### Instructions

One file per subject, named for the subject. These are **always-on** documents: once installed
they load at the start of every session in the project they were copied into, so each one must
earn permanent context. Guidance that only matters while performing a particular task belongs in
a skill, which loads on demand, or in this README, which is read by people.

Write each one as a **paper of commands**, not a description of how things are:

- open with an **Objective** stating what the instruction achieves and why, then a **Your tasks**
  line naming the actions to perform;
- give each action its own numbered section, titled with the imperative verb;
- write every rule as a command with its condition attached — "Index a term only when all three
  hold", not "a term is admitted when";
- name any file the agent owns by a path **relative to the project root**, and say plainly that
  creating it is the agent's job rather than a precondition to wait on;
- never reference this repository, an installed location, or another project's configuration file.
  Where the instruction is read from varies with the environment; what it commands does not.

## Install

`install.sh` copies everything here into a **target project** you pass as an argument. One run
writes both clients' project-local shapes.

```bash
./install.sh /path/to/project
./install.sh /path/to/project execution-planning
./install.sh /path/to/project execution-planning,another-skill
```

Omit the skill list to install every skill. A comma-separated list installs only those
named skills; an unknown name is an error. Instructions are always installed.

The script refuses to install into this repository itself.

| | Destination |
| --- | --- |
| **Skills** | `<project>/.agents/skills/<name>/` |
| **Cursor rules** | `<project>/.cursor/rules/<name>.mdc` |
| **Claude Code rules** | `<project>/.claude/rules/<name>.md` |

Cursor and Codex load `.agents/skills/` natively. Claude Code's documented project skill path is
`.claude/skills/`; this install does not write a second skill copy there, because Cursor also
scans that directory and would register the same skill twice.

Instructions are given to each client in the shape it loads: verbatim for Claude Code, and wrapped
in `description` / `alwaysApply` frontmatter for Cursor. A `README.md` in a source directory is
never installed.

Paths written inside a skill are relative to the *consuming* project's root —
`.agents/skills/<name>/scripts/…` — because that is where the shell starts.

Where a destination already exists the script lists every collision and asks once, defaulting to
overwrite; answering `n` skips all existing items and installs the rest. Skill folders are replaced
whole, so a file deleted here does not survive in an install.

Restart the client afterwards — skills and rules are read at session start.

If an earlier install left copies at **user scope**, the script prints `rm` commands for those
paths and does not delete them. Run the printed commands if you no longer want those skills and
rules applied to every project on the machine:

```bash
rm -rf ~/.cursor/skills/execution-planning
rm -rf ~/.claude/skills/execution-planning
rm -f  ~/.cursor/rules/terminology-discipline.mdc \
       ~/.cursor/rules/problem-presentation-format.mdc
rm -f  ~/.claude/rules/terminology-discipline.md \
       ~/.claude/rules/problem-presentation-format.md
```

## Contributing back

Anything added here must be **general**: it must make sense in a repository that knows nothing
about the project it came from. A skill or instruction that names a specific spec file, product, or
directory layout belongs in that project, not in this one. Where a rule is genuinely useful but
carries a project-specific detail, state the rule by the role the artifact plays rather than by its
path — and never by the location it happens to be installed to, which varies with the environment.
