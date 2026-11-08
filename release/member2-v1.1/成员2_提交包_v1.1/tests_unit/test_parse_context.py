"""验证真实34题契约、结构声明与不可裁上下文，不把静态骨架当编译结论。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.src.parse import parse_task
from agent.src.task_card import build_context, make_skeleton


class ParseContextTests(unittest.TestCase):
    def test_all_source_tasks_preserved(self):
        paths = sorted((ROOT / "data" / "tasks").glob("*.yaml"))
        self.assertEqual(len(paths), 34)
        for path in paths:
            card = parse_task(path)
            self.assertEqual(card["task_id"], path.stem)
            self.assertEqual(card["task_version"], hashlib.sha256(path.read_bytes()).hexdigest()[:8])
            self.assertFalse(card["missing_fields"], path.stem)
            self.assertTrue(card["spec_text"], path.stem)
            self.assertFalse(card["skeleton_compiled"])
            self.assertNotIn(str(ROOT), card["source_path"])
            self.assertIn("END_FUNCTION_BLOCK", make_skeleton(card))

    def test_structured_fields_are_declared_once(self):
        p08 = parse_task(ROOT / "data/tasks/P08.yaml")
        skeleton = make_skeleton(p08)
        self.assertIn("TYPE ST_AnalogChannel", skeleton)
        self.assertIn("channels : ARRAY[*] OF ST_AnalogChannel;", skeleton)
        self.assertNotIn("channels[].", skeleton)
        self.assertEqual(skeleton.count("enable : BOOL;"), 1)
        self.assertEqual(len(p08["io_table"]), 10)
        self.assertEqual(len(p08["interface_io_table"]), 3)
        p17 = parse_task(ROOT / "data/tasks/P17.yaml")
        skeleton17 = make_skeleton(p17)
        self.assertIn("TYPE ST_Recipe", skeleton17)
        self.assertEqual(skeleton17.count("recipeID : INT;"), 1)
        self.assertIn("recipe : ARRAY[1..10] OF ST_Recipe;", skeleton17)

    def test_conflicts_remain_visible(self):
        for tid in ("P08", "P17", "P19"):
            card = parse_task(ROOT / f"data/tasks/{tid}.yaml")
            self.assertTrue(card["degraded"], tid)
            self.assertTrue(card["semantic_warnings"], tid)
        p18 = parse_task(ROOT / "data/tasks/P18.yaml")
        self.assertIn("item : VARIANT;", make_skeleton(p18))
        self.assertTrue(p18["dialect_requirements"])

    def test_optional_context_is_removed_before_required(self):
        card = parse_task(ROOT / "data/tasks/S01.yaml")
        basic = build_context(card, budget=100000)
        budget = basic["estimated_tokens"] + 50
        result = build_context(card, reference="REF " * 500, feedback="ERROR " * 500, budget=budget)
        self.assertFalse(result["overflow"])
        self.assertIn(card["requirement"], result["user"])
        self.assertIn(card["spec_text"], result["user"])
        dropped = [x["section"] for x in result["trace"] if x["action"] == "drop"]
        self.assertEqual(dropped, ["reference", "feedback"])
        self.assertNotIn("REF REF", result["user"])
        overflow = build_context(card, budget=1)
        self.assertTrue(overflow["overflow"])
        self.assertIn(card["requirement"], overflow["user"])
        self.assertIn(card["spec_text"], overflow["user"])

    def test_missing_contract_is_not_guessed(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix="tmp_parse_test_") as tmp:
            path = Path(tmp) / "task.json"
            path.write_text(json.dumps({"task_id": "S99", "notes": "保留备注"}), encoding="utf-8")
            card = parse_task(path)
            self.assertTrue(card["degraded"])
            self.assertIn("requirement", card["missing_fields"])
            self.assertIsNone(card["requirement"])
            self.assertEqual(card["notes"], "保留备注")

    def test_invalid_rows_degrade_without_inventing_types(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix="tmp_parse_test_") as tmp:
            path = Path(tmp) / "task.json"
            path.write_text(json.dumps({
                "task_id": "P19", "constraints": 1,
                "io_table": [{"name": "x", "direction": "IN"}],
            }), encoding="utf-8")
            card = parse_task(path)
            self.assertTrue(card["degraded"])
            self.assertEqual(card["interface_io_table"], [])
            self.assertTrue(card["warnings"])


if __name__ == "__main__":
    unittest.main()
