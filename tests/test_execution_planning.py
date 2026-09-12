"""Tests for the execution-planning skill's scripts.

Run from the repository root:

    python3 -m unittest discover tests
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "execution-planning" / "scripts"
TASK_DAG = SCRIPTS / "task_dag.py"
CHECK_PLAN = SCRIPTS / "check_plan.py"
GOOD_PLAN = ROOT / "tests" / "fixtures" / "good_plan.md"

sys.path.insert(0, str(SCRIPTS))

import plan_doc  # noqa: E402
import task_dag  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], capture_output=True, text=True, cwd=ROOT
    )


SAMPLE = [
    "--goal-order", "setup,ship",
    "--task", "setup:code:parser",
    "--task", "setup:config:ci",
    "--task", "ship:docs:notes",
    "parser > ci",
]


class TaskDagTest(unittest.TestCase):
    def test_table_is_six_static_columns(self):
        result = run(str(TASK_DAG), "--format", "table", *SAMPLE)
        self.assertEqual(result.returncode, 0, result.stderr)
        header = result.stdout.splitlines()[0]
        self.assertEqual(
            header,
            "| Task # | Goal | Category | Task | Depends on | Success criterion |",
        )

    def test_table_carries_no_run_state(self):
        result = run(str(TASK_DAG), "--format", "table", *SAMPLE)
        for word in ("Unblocks", "Status", "pending"):
            self.assertNotIn(word, result.stdout)

    def test_goal_cut_is_inserted_between_goals(self):
        result = run(str(TASK_DAG), "--format", "pairs", *SAMPLE)
        self.assertIn("ci > notes", result.stdout)

    def test_goal_cut_survives_the_column_change(self):
        """Rendering changed; graph construction did not."""
        dag = task_dag.build(
            [("parser", "ci")],
            [
                task_dag.Slice("parser", "setup", "code"),
                task_dag.Slice("ci", "setup", "config"),
                task_dag.Slice("notes", "ship", "docs"),
            ],
            ["setup", "ship"],
        )
        self.assertEqual(dag["cut_edges"], [("ci", "notes")])
        self.assertEqual([t["label"] for t in dag["tasks"]], ["T1", "T2", "T3"])

    def test_slice_flag_still_accepted(self):
        with_task = run(str(TASK_DAG), "--format", "table", "--task", "g:code:a", "--task", "g:config:b", "a > b")
        with_slice = run(str(TASK_DAG), "--format", "table", "--slice", "g:code:a", "--slice", "g:config:b", "a > b")
        self.assertEqual(with_task.stdout, with_slice.stdout)
        self.assertEqual(with_task.returncode, 0)

    def test_cycle_is_rejected(self):
        result = run(str(TASK_DAG), "--task", "g:code:a", "--task", "g:config:b", "a > b", "b > a")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cycle detected", result.stderr)

    def test_second_task_in_one_goal_and_category_is_rejected(self):
        result = run(str(TASK_DAG), "--task", "g:code:a", "--task", "g:code:b")
        self.assertEqual(result.returncode, 1)
        self.assertIn("two tasks in goal", result.stderr)

    def test_cross_goal_pair_is_rejected(self):
        result = run(str(TASK_DAG), "--goal-order", "one,two", "--task", "one:code:a", "--task", "two:code:b", "a > b")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cross-goal pair", result.stderr)

    def test_scaffold_carries_guidance_not_a_run_loop(self):
        result = run(str(TASK_DAG), "--format", "scaffold", "--title", "x", *SAMPLE)
        self.assertIn("## Execution Guidelines", result.stdout)
        self.assertNotIn("## Execution Protocol", result.stdout)
        self.assertNotIn("Status is only", result.stdout)
        self.assertNotIn("**Waivers**", result.stdout)


class PlanDocTest(unittest.TestCase):
    def setUp(self):
        self.doc = plan_doc.load(str(GOOD_PLAN))

    def test_task_subsections_are_inside_the_tasks_section(self):
        """A `###` heading must not truncate its parent `##` section."""
        self.assertEqual([b.label for b in self.doc.task_bodies], ["T1", "T2", "T3"])
        self.assertEqual([b.id for b in self.doc.task_bodies], ["parser", "ci", "notes"])

    def test_body_fields_are_captured(self):
        body = self.doc.task_bodies[0]
        self.assertEqual(sorted(body.fields), ["Consumes", "Files", "Produces", "Verify"])
        self.assertIn("- src/parser.py", body.fields["Files"])

    def test_tables_are_found_by_section(self):
        dag = self.doc.table_with_headers("Task DAG", [
            "Task #", "Goal", "Category", "Task", "Depends on", "Success criterion",
        ])
        self.assertIsNotNone(dag)
        self.assertEqual(len(dag.rows), 3)

    def test_em_dash_reads_as_no_references(self):
        self.assertEqual(plan_doc.split_refs("—"), [])
        self.assertEqual(plan_doc.split_refs("T1, T2"), ["T1", "T2"])


class CheckPlanTest(unittest.TestCase):
    def check(self, text: str, *extra: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.md"
            path.write_text(text)
            return run(str(CHECK_PLAN), *extra, str(path))

    def mutate(self, old: str, new: str) -> subprocess.CompletedProcess[str]:
        text = GOOD_PLAN.read_text()
        self.assertEqual(text.count(old), 1, f"fixture anchor is not unique: {old!r}")
        return self.check(text.replace(old, new))

    def test_good_plan_passes(self):
        result = run(str(CHECK_PLAN), str(GOOD_PLAN))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.strip(), "")

    def assert_reports(self, result: subprocess.CompletedProcess[str], needle: str) -> None:
        self.assertEqual(result.returncode, 1, f"expected a violation, got none:\n{result.stdout}")
        self.assertIn(needle, result.stdout)

    def test_hand_edited_numbering(self):
        self.assert_reports(
            self.mutate("| T2 | setup | config | ci | T1 |", "| T4 | setup | config | ci | T1 |"),
            "is not T1..T3 in order",
        )

    def test_dependency_on_a_task_that_does_not_exist(self):
        self.assert_reports(
            self.mutate("| ci | T1 |", "| ci | T9 |"),
            "which is not a Task # in this plan",
        )

    def test_dropped_edge_fails_the_rebuild(self):
        self.assert_reports(
            self.mutate("| T3 | ship | docs | notes | T2 |", "| T3 | ship | docs | notes | — |"),
            "Depends on should be 'T2'",
        )

    def test_missing_success_criterion(self):
        self.assert_reports(
            self.mutate("| `README.md` documents the parser entry point and its two flags |", "|  |"),
            "has no success criterion",
        )

    def test_blank_goals_cell(self):
        self.assert_reports(self.mutate("| ship | T3 |", "| ship |  |"), "blank Tasks cell")

    def test_goals_disagree_with_the_dag(self):
        self.assert_reports(self.mutate("| setup | T1, T2 |", "| setup | T1 |"), "the DAG has")

    def test_used_category_without_an_executor(self):
        self.assert_reports(
            self.mutate("| docs | main-agent | The README wording is a judgement about what users need to know |\n", ""),
            "has no Category Assignment row",
        )

    def test_executor_is_not_an_agent(self):
        self.assert_reports(
            self.mutate("| config | main-agent |", "| config | whoever is free |"),
            "must be main-agent or subagent:<type>",
        )

    def test_blank_model_cell(self):
        self.assert_reports(
            self.mutate("| T2 | cursor-grok-4.6-medium |", "| T2 |  |"),
            "blank Model cell",
        )

    def test_named_model_needs_the_flag(self):
        text = GOOD_PLAN.read_text().replace("| T1 | cursor-grok-4.6-high |", "| T1 | claude-opus-5-high |")
        self.assert_reports(self.check(text), "use --allow-model when the user named it")
        self.assertEqual(self.check(text, "--allow-model", "claude-opus-5-high").returncode, 0)

    def test_file_outside_the_task_category(self):
        self.assert_reports(
            self.mutate("- src/parser.py", "- docs/parser-notes.md"),
            "is a code task but Files names",
        )

    def test_body_missing_a_field(self):
        self.assert_reports(
            self.mutate("**Verify**\n\n- `grep -n \"parse_config\" README.md`", "- nothing to verify"),
            "body has no **Verify**",
        )

    def test_spec_sync_drives_from_a_task_that_does_not_exist(self):
        self.assert_reports(
            self.mutate("| amend | T3 |", "| amend | T7 |"),
            "which is not on the DAG",
        )

    def test_leftover_placeholder(self):
        self.assert_reports(
            self.mutate("- .github/workflows/ci.yml", "- <path in this task's category>"),
            "unfilled placeholder",
        )

    def test_old_run_board_columns_are_rejected(self):
        self.assert_reports(
            self.mutate(
                "| Task # | Goal | Category | Task | Depends on | Success criterion |",
                "| Task # | Goal | Category | Task | Depends on | Unblocks | Success criterion | Status |",
            ),
            "Task DAG columns must be",
        )

    def test_two_tasks_in_one_goal_and_category(self):
        self.assert_reports(
            self.mutate("| T2 | setup | config | ci |", "| T2 | setup | code | ci |"),
            "has two code tasks",
        )

    def test_missing_section(self):
        self.assert_reports(self.mutate("\n## Spec Sync\n", "\n## Spec Notes\n"), "missing required section")


if __name__ == "__main__":
    unittest.main()
