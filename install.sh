#!/usr/bin/env bash
#
# Install this repository's skills and instructions at user scope, where every
# project on the machine picks them up.
#
# Each client is given the content in the shape it actually loads: skill folders
# copied whole, instruction documents copied verbatim for Claude Code and wrapped
# in Cursor's rule frontmatter for Cursor.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'EOF'
Usage: install.sh [--all | --claude | --cursor]

  --all       install for both clients (default)
  --claude    install for Claude Code only
  --cursor    install for Cursor only
  -h, --help  show this message

Destinations:
  Claude Code   ~/.claude/skills/<name>/    ~/.claude/rules/<name>.md
  Cursor        ~/.cursor/skills/<name>/    ~/.cursor/rules/<name>.mdc

macOS only.
EOF
}

# ---------------------------------------------------------------- preconditions

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "error: macOS only (found $(uname -s))" >&2
    exit 1
fi

targets=()
case "${1:---all}" in
    --all)      targets=(claude cursor) ;;
    --claude)   targets=(claude) ;;
    --cursor)   targets=(cursor) ;;
    -h|--help)  usage; exit 0 ;;
    *)          echo "error: unknown argument '$1'" >&2; echo >&2; usage >&2; exit 1 ;;
esac

if [[ $# -gt 1 ]]; then
    echo "error: one argument at most (got $#)" >&2
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
    [[ "$(basename "$file")" == "README.md" ]] && continue
    instructions+=("$file")
done

if [[ ${#skills[@]} -eq 0 && ${#instructions[@]} -eq 0 ]]; then
    echo "error: nothing to install — no skills or instructions found under $SRC" >&2
    exit 1
fi

skills_root_for()       { [[ "$1" == claude ]] && echo "$HOME/.claude/skills" || echo "$HOME/.cursor/skills"; }
instructions_root_for() { [[ "$1" == claude ]] && echo "$HOME/.claude/rules"  || echo "$HOME/.cursor/rules"; }
instruction_ext_for()   { [[ "$1" == claude ]] && echo "md" || echo "mdc"; }

# ------------------------------------------------------------ collision handling

# Every destination that already exists is gathered before anything is written,
# so the user answers one question about the whole run rather than one per item.
collisions=()
for target in "${targets[@]}"; do
    for skill in "${skills[@]}"; do
        dest="$(skills_root_for "$target")/$(basename "$skill")"
        [[ -e "$dest" ]] && collisions+=("$dest")
    done
    for instruction in "${instructions[@]}"; do
        name="$(basename "$instruction" .md)"
        dest="$(instructions_root_for "$target")/${name}.$(instruction_ext_for "$target")"
        [[ -e "$dest" ]] && collisions+=("$dest")
    done
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

for target in "${targets[@]}"; do
    skills_root="$(skills_root_for "$target")"
    instructions_root="$(instructions_root_for "$target")"
    ext="$(instruction_ext_for "$target")"

    mkdir -p "$skills_root" "$instructions_root"
    echo "== $target"

    for skill in "${skills[@]}"; do
        name="$(basename "$skill")"
        dest="$skills_root/$name"
        if should_write "$dest"; then
            # Replaced whole, so a file deleted upstream cannot survive here.
            rm -rf "$dest"
            cp -R "$skill" "$dest"
            echo "   skill        $name -> $dest"
            installed=$((installed + 1))
        else
            echo "   skill        $name -- skipped (exists)"
            skipped=$((skipped + 1))
        fi
    done

    for instruction in "${instructions[@]}"; do
        name="$(basename "$instruction" .md)"
        dest="$instructions_root/${name}.${ext}"
        if should_write "$dest"; then
            if [[ "$target" == cursor ]]; then
                write_cursor_rule "$instruction" "$dest"
            else
                cp "$instruction" "$dest"
            fi
            echo "   instruction  $name -> $dest"
            installed=$((installed + 1))
        else
            echo "   instruction  $name -- skipped (exists)"
            skipped=$((skipped + 1))
        fi
    done
    echo
done

# ----------------------------------------------------------------------- report

echo "Installed $installed item(s), skipped $skipped."

for target in "${targets[@]}"; do
    if [[ "$target" == cursor ]]; then
        echo
        echo "Note: Cursor's global rules directory (~/.cursor/rules) is community-documented;"
        echo "      the official docs describe User Rules only through Customize -> Rules."
        echo "      Confirm the rules appear there, and move them if Cursor expects elsewhere."
    fi
done

echo
echo "Restart the client — skills and rules are read at session start."
