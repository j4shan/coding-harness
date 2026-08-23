#!/usr/bin/env bash
#
# Install this repository's skills and instructions into a target project.
#
# Each client is given the content in the shape it actually loads: skill folders
# copied whole into .agents/skills/, instruction documents copied verbatim for
# Claude Code and wrapped in Cursor's rule frontmatter for Cursor.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'EOF'
Usage: install.sh <project-dir> [skill,skill,...]

Copy skills and instructions into <project-dir> at the paths each client
reads for that project.

  <project-dir>        target project root (required)
  [skill,skill,...]    install only these skills (comma-separated names).
                       Omit to install every skill.
  -h, --help           show this message

Destinations:
  Skills          <project>/.agents/skills/<name>/
  Cursor rules    <project>/.cursor/rules/<name>.mdc
  Claude rules    <project>/.claude/rules/<name>.md
EOF
}

# ---------------------------------------------------------------- preconditions

if [[ $# -eq 1 && ( "$1" == -h || "$1" == --help ) ]]; then
    usage
    exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "error: project directory required, optional skill list (got $# argument(s))" >&2
    echo >&2
    usage >&2
    exit 1
fi

if [[ "$1" == -* ]]; then
    echo "error: unknown argument '$1'" >&2
    echo >&2
    usage >&2
    exit 1
fi

if [[ $# -eq 2 && "$2" == -* ]]; then
    echo "error: unknown argument '$2'" >&2
    echo >&2
    usage >&2
    exit 1
fi

skill_filter="${2-}"

if [[ ! -d "$1" ]]; then
    echo "error: not a directory: $1" >&2
    exit 1
fi

PROJECT="$(cd "$1" && pwd)"

if [[ "$PROJECT" == "$SRC" ]]; then
    echo "error: refuse to install into this repository ($SRC)" >&2
    exit 1
fi

# ------------------------------------------------------------------ what to copy

# A skill is any directory carrying a SKILL.md. Selecting on the marker file
# rather than on "every directory" is what keeps skills/README.md out without
# naming it.
skills=()
for dir in "$SRC"/skills/*/; do
    [[ -f "${dir}SKILL.md" ]] && skills+=("${dir%/}")
done

# README.md documents the directory for a human reading the repository; it is not
# an instruction and must not be installed as one.
instructions=()
for file in "$SRC"/instructions/*.md; do
    [[ -f "$file" ]] || continue
    [[ "$(basename "$file")" == "README.md" ]] && continue
    instructions+=("$file")
done

if [[ -n "$skill_filter" ]]; then
    compact="${skill_filter//[[:space:]]/}"
    if [[ "$compact" == ,* || "$compact" == *, || "$compact" == *,,* ]]; then
        echo "error: empty skill name in list: $skill_filter" >&2
        exit 1
    fi

    requested=()
    IFS=',' read -ra raw <<< "$skill_filter"
    for token in "${raw[@]}"; do
        name="${token#"${token%%[![:space:]]*}"}"
        name="${name%"${name##*[![:space:]]}"}"
        if [[ -z "$name" ]]; then
            echo "error: empty skill name in list: $skill_filter" >&2
            exit 1
        fi
        requested+=("$name")
    done

    selected=()
    seen_csv=
    for name in "${requested[@]}"; do
        case ",$seen_csv," in
            *",$name,"*) continue ;;
        esac
        seen_csv="${seen_csv:+$seen_csv,}$name"

        found=
        for skill in "${skills[@]}"; do
            if [[ "$(basename "$skill")" == "$name" ]]; then
                selected+=("$skill")
                found=1
                break
            fi
        done
        if [[ -z "$found" ]]; then
            echo "error: unknown skill '$name'" >&2
            echo "available:" >&2
            for skill in "${skills[@]}"; do
                echo "  $(basename "$skill")" >&2
            done
            exit 1
        fi
    done
    skills=("${selected[@]}")
fi

if [[ ${#skills[@]} -eq 0 && ${#instructions[@]} -eq 0 ]]; then
    echo "error: nothing to install — no skills or instructions found under $SRC" >&2
    exit 1
fi

skills_root="$PROJECT/.agents/skills"
cursor_rules_root="$PROJECT/.cursor/rules"
claude_rules_root="$PROJECT/.claude/rules"

# ------------------------------------------------------------ collision handling

# Every destination that already exists is gathered before anything is written,
# so the user answers one question about the whole run rather than one per item.
collisions=()
for skill in "${skills[@]}"; do
    dest="$skills_root/$(basename "$skill")"
    [[ -e "$dest" ]] && collisions+=("$dest")
done
for instruction in "${instructions[@]}"; do
    name="$(basename "$instruction" .md)"
    [[ -e "$cursor_rules_root/${name}.mdc" ]] && collisions+=("$cursor_rules_root/${name}.mdc")
    [[ -e "$claude_rules_root/${name}.md" ]] && collisions+=("$claude_rules_root/${name}.md")
done

overwrite=yes
if [[ ${#collisions[@]} -gt 0 ]]; then
    echo "Already present:"
    printf '  %s\n' "${collisions[@]}"
    echo
    read -r -p "${#collisions[@]} existing item(s) will be overwritten. Overwrite? [Y/n] " answer
    case "${answer:-Y}" in
        [Yy]*)  overwrite=yes ;;
        *)      overwrite=no; echo "Skipping all existing items." ;;
    esac
    echo
fi

# Returns 0 when the destination should be written.
should_write() {
    [[ ! -e "$1" || "$overwrite" == yes ]]
}

# ------------------------------------------------------------------- conversion

# Cursor loads a rule only if it carries frontmatter telling it when to apply.
# The description is the document's H1, so the agent has something to match on.
write_cursor_rule() {
    local source="$1" dest="$2" description
    description="$(sed -n 's/^# //p' "$source" | head -1)"
    [[ -z "$description" ]] && description="$(basename "$source" .md)"

    {
        printf -- '---\n'
        printf 'description: %s\n' "$description"
        printf 'alwaysApply: true\n'
        printf -- '---\n\n'
        cat "$source"
    } > "$dest"
}

# ---------------------------------------------------------------------- install

installed=0
skipped=0

mkdir -p "$skills_root" "$cursor_rules_root" "$claude_rules_root"

echo "== $PROJECT"

for skill in "${skills[@]}"; do
    name="$(basename "$skill")"
    dest="$skills_root/$name"
    if should_write "$dest"; then
        # Replaced whole, so a file deleted upstream cannot survive here.
        rm -rf "$dest"
        cp -R "$skill" "$dest"
        echo "   skill             $name -> $dest"
        installed=$((installed + 1))
    else
        echo "   skill             $name -- skipped (exists)"
        skipped=$((skipped + 1))
    fi
done

for instruction in "${instructions[@]}"; do
    name="$(basename "$instruction" .md)"

    dest="$cursor_rules_root/${name}.mdc"
    if should_write "$dest"; then
        write_cursor_rule "$instruction" "$dest"
        echo "   instruction/cursor $name -> $dest"
        installed=$((installed + 1))
    else
        echo "   instruction/cursor $name -- skipped (exists)"
        skipped=$((skipped + 1))
    fi

    dest="$claude_rules_root/${name}.md"
    if should_write "$dest"; then
        cp "$instruction" "$dest"
        echo "   instruction/claude $name -> $dest"
        installed=$((installed + 1))
    else
        echo "   instruction/claude $name -- skipped (exists)"
        skipped=$((skipped + 1))
    fi
done

echo

# ----------------------------------------------------------------------- report

echo "Installed $installed item(s), skipped $skipped."

echo
echo "Restart the client — skills and rules are read at session start."

# -------------------------------------------------------- user-scope leftovers

leftover_dirs=()
leftover_files=()
for skill in "${skills[@]}"; do
    name="$(basename "$skill")"
    [[ -e "$HOME/.cursor/skills/$name" ]] && leftover_dirs+=("$HOME/.cursor/skills/$name")
    [[ -e "$HOME/.claude/skills/$name" ]] && leftover_dirs+=("$HOME/.claude/skills/$name")
done
for instruction in "${instructions[@]}"; do
    name="$(basename "$instruction" .md)"
    [[ -e "$HOME/.cursor/rules/${name}.mdc" ]] && leftover_files+=("$HOME/.cursor/rules/${name}.mdc")
    [[ -e "$HOME/.claude/rules/${name}.md" ]] && leftover_files+=("$HOME/.claude/rules/${name}.md")
done

echo
if [[ ${#leftover_dirs[@]} -eq 0 && ${#leftover_files[@]} -eq 0 ]]; then
    echo "No user-scope leftovers from an earlier install."
else
    echo "User-scope leftovers from an earlier install (safe to remove if you no longer"
    echo "want these applied to every project):"
    echo
    for dest in "${leftover_dirs[@]}"; do
        echo "  rm -rf $dest"
    done
    for dest in "${leftover_files[@]}"; do
        echo "  rm -f $dest"
    done
fi
