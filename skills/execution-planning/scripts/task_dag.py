#!/usr/bin/env python3
"""Turn immediate task dependencies into a topologically ordered task table.

Input is a list of dependency pairs, each meaning "prerequisite > dependent".
Output is a markdown table: one row per task, carrying both directions of every
edge, so a reader can answer "can this start?" and "what did finishing it
unblock?" without redrawing the graph. Task ids are `T1..Tn` in topological
order, so a prerequisite always appears above everything that depends on it.

The table is the whole representation - there is deliberately no rendered graph
and no wave schedule. Waves would impose synchronization barriers the
dependencies do not require, and choosing a concurrency model is the plan
executor's call, not this tool's.

Usage:
    task_dag.py "audit > design" "survey > design" "design > build" --task docs
    task_dag.py --format scaffold --title "Add caching" "audit > design"
    echo '{"tasks": ["a"], "edges": [["a", "b"]]}' | task_dag.py
    task_dag.py --format table "a > b"

Exits 1 on a cycle, printing the cycle path.
"""

from __future__ import annotations

import argparse
import json
import sys

SEPARATORS = ("->", ">")


def parse_pair(raw: str) -> tuple[str, str]:
    for sep in SEPARATORS:
        if sep in raw:
            head, _, tail = raw.partition(sep)
            head, tail = head.strip(), tail.strip()
            if not head or not tail:
                raise ValueError(f"incomplete dependency pair: {raw!r}")
            return head, tail
    raise ValueError(f"not a dependency pair (expected 'A > B'): {raw!r}")


def build(edges: list[tuple[str, str]], extra_tasks: list[str]) -> dict:
    """Number tasks in topological order. Declaration order breaks ties, so runs are stable.

    Tasks are peeled off in ready-sets rather than one at a time. That is purely an
    ordering device - it keeps mutually independent tasks adjacent in the numbering,
    which reads better than a depth-first order - and carries no scheduling meaning.
    """
    order_seen: list[str] = []
    for name in [n for pair in edges for n in pair] + extra_tasks:
        if name not in order_seen:
            order_seen.append(name)

    prereqs: dict[str, list[str]] = {name: [] for name in order_seen}
    dependents: dict[str, list[str]] = {name: [] for name in order_seen}
    for src, dst in dict.fromkeys(edges):  # dedupe, keep order
        prereqs[dst].append(src)
        dependents[src].append(dst)

    ordered: list[str] = []
    placed: set[str] = set()
    remaining = list(order_seen)
    while remaining:
        ready = [n for n in remaining if all(p in placed for p in prereqs[n])]
        if not ready:
            raise ValueError(f"cycle detected: {' > '.join(find_cycle(prereqs, remaining))}")
        ordered += ready
        placed.update(ready)
        remaining = [n for n in remaining if n not in placed]

    # Numbers stay ints so every sort key below is numeric; `label` is the display
    # form. Keeping them apart is what stops "T10" from sorting before "T9".
    numbers = {name: i for i, name in enumerate(ordered, start=1)}
    labels = {name: f"T{numbers[name]}" for name in ordered}
    return {
        "tasks": [
            {
                "number": numbers[name],
                "label": labels[name],
                "id": name,
                "prereqs": sorted(prereqs[name], key=lambda p: numbers[p]),
                "dependents": sorted(dependents[name], key=lambda d: numbers[d]),
            }
            for name in ordered
        ],
        "numbers": numbers,
        "labels": labels,
        "edges": list(dict.fromkeys(edges)),
    }


def find_cycle(prereqs: dict[str, list[str]], scope: list[str]) -> list[str]:
    """Return one cycle among the unplaceable tasks, in prerequisite > dependent order."""
    path: list[str] = []
    seen: set[str] = set()
    node = scope[0]
    while node not in seen:
        seen.add(node)
        path.append(node)
        candidates = [p for p in prereqs[node] if p in scope]
        if not candidates:
            return path[::-1]
        node = candidates[0]
    cycle = path[path.index(node):] + [node]
    return cycle[::-1]


def render_table(dag: dict) -> str:
    """The DAG as markdown, one row per task, emitted unfenced so it renders as a table.

    Both edge directions are present on purpose. `Depends on` answers "can this
    start yet?" at dispatch time; `Unblocks` answers "what did finishing it release?"
    Either column alone forces the reader to invert the table in their head.
    """
    labels = dag["labels"]
    lines = [
        "| Task # | Task | Depends on | Unblocks | Success criterion | Status |",
        "|---|---|---|---|---|---|",
    ]
    for task in dag["tasks"]:
        depends = ", ".join(labels[p] for p in task["prereqs"]) or "—"
        unblocks = ", ".join(labels[d] for d in task["dependents"]) or "—"
        lines.append(
            f"| {task['label']} | {task['id']} | {depends} | {unblocks} "
            "| <what done means> | pending |"
        )
    return "\n".join(lines)


def render_pairs(dag: dict) -> str:
    width = max((len(src) for src, _ in dag["edges"]), default=0)
    lines = ["Immediate dependencies (`prerequisite > dependent`):", "", "```"]
    lines += [f"{src.ljust(width)} > {dst}" for src, dst in dag["edges"]]
    lines.append("```")
    return "\n".join(lines)


def render_scaffold(dag: dict, title: str) -> str:
    """Emit the whole plan document with every generated cell already filled in."""
    assignment = [
        "| Task # | Executor | Model | Rationale |",
        "|---|---|---|---|",
    ]
    for task in dag["tasks"]:  # placeholders avoid '|' - it would split the cell
        assignment.append(
            f"| {task['label']} "
            "| <main-agent or subagent:type> | <Sonnet / high or Opus / medium> | <why> |"
        )

    return "\n".join(
        [
            f"# Execution Plan — {title}",
            "",
            "## Problem Statement",
            "",
            "<what is broken or missing today, and why it is worth changing>",
            "",
            "**Goals**",
            "",
            "- <goal>",
            "",
            "**Non-goals** <!-- omit this block entirely unless the user supplied non-goals -->",
            "",
            "- <non-goal>",
            "",
            "## Task DAG",
            "",
            render_table(dag),
            "",
            "## Task Assignment",
            "",
            *assignment,
            "",
            "## Execution Protocol",
            "",
            "Two things are fixed: the dependency edges above, and the executor and model",
            "assigned to each task. Everything else about how the run is paced is the",
            "executor's call.",
            "",
            "Start any task whose `Depends on` entries are all `done`, marking its row",
            "`in_progress` and then `done` or `failed`. When several become ready together,",
            "launch the `subagent:` ones in a single message with multiple `Agent` calls so",
            "they genuinely run in parallel. A task never waits on anything absent from its",
            "`Depends on` cell.",
            "",
            "On a failure, everything reachable downstream is blocked and the rest of the",
            "graph continues. Record here anything waived, and why.",
        ]
    )


RENDERERS = {
    "table": render_table,
    "pairs": render_pairs,
    "json": lambda dag: json.dumps({"tasks": dag["tasks"]}, indent=2),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pairs", nargs="*", help="dependency pairs, 'prerequisite > dependent'")
    parser.add_argument("--task", action="append", default=[], help="task with no dependencies")
    parser.add_argument(
        "--format",
        choices=["all", "scaffold", *RENDERERS],
        default="all",
        help="output section; 'scaffold' emits the full plan document (default: all)",
    )
    parser.add_argument("--title", default="<objective>", help="plan title, for --format scaffold")
    args = parser.parse_args()

    pairs, tasks = list(args.pairs), list(args.task)
    if not sys.stdin.isatty() and not pairs:
        payload = json.loads(sys.stdin.read() or "{}")
        pairs += [f"{src} > {dst}" for src, dst in payload.get("edges", [])]
        tasks += payload.get("tasks", [])

    try:
        edges = [parse_pair(raw) for raw in pairs]
        dag = build(edges, tasks)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not dag["tasks"]:
        print("error: no tasks given", file=sys.stderr)
        return 1

    if args.format == "scaffold":
        print(render_scaffold(dag, args.title))
        return 0

    if args.format != "all":
        print(RENDERERS[args.format](dag))
        return 0

    print(render_table(dag))
    print()
    print(render_pairs(dag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
