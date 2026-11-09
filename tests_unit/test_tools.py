"""工具协议与超时的独立契约测试；不宣称实测 PLC 编译器。"""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agent" / "scripts"))
from agent.src.tools import Toolchain, normalize_errors, run_process
from st_bundle import split_source


class ToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / ".test_tmp").mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        (ROOT / ".test_tmp").rmdir()

    def test_five_known_diagnostics(self):
        samples = [
            ("p.st:8:3: error: undeclared variable Motor", "E_UNDECLARED", 8, "error"),
            ("p.st(12,4): error: type mismatch BOOL and INT", "E_TYPE", 12, "error"),
            ("error: library Standard not found", "E_LIBRARY", None, "error"),
            ("line 9: syntax error unexpected END_IF", "E_SYNTAX", 9, "error"),
            ("line 17: warning: unreachable dead code", "W_DEAD_CODE", 17, "warning"),
        ]
        for raw, code, line, severity in samples:
            with self.subTest(raw=raw):
                item = normalize_errors(raw)[0]
                self.assertEqual((item["code"], item["line"], item["severity"]), (code, line, severity))
                self.assertEqual(set(item), {"code", "severity", "line", "message", "raw"})

    def test_process_hard_timeout(self):
        started = time.monotonic()
        result = run_process([sys.executable, "-c", "import time; time.sleep(10)"], timeout_s=0.15)
        self.assertEqual(result["status"], "timeout")
        self.assertLess(time.monotonic() - started, 5)

    def test_missing_command_is_tool_error(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".test_tmp") as tmp:
            chain = Toolchain({}, time.monotonic() + 10, tmp)
            result = chain.compile("PROGRAM P\nEND_PROGRAM", "missing")
            self.assertEqual(result["status"], "tool_error")
            self.assertFalse(result["authoritative_available"])
            self.assertEqual(chain.test("", "none")["status"], "skipped")

    def _command(self, payload, returncode=0):
        script = "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text(" + repr(json.dumps(payload)) + ", encoding='utf-8'); sys.exit(" + str(returncode) + ")"
        return [sys.executable, "-c", script, "{result}"]

    def test_authority_requires_json_even_when_exit_zero(self):
        cfg = {"authoritative": {"command": [sys.executable, "-c", "print('0 errors')"]}}
        with tempfile.TemporaryDirectory(dir=ROOT / ".test_tmp") as tmp:
            result = Toolchain(cfg, time.monotonic() + 10, tmp).compile("", "no_result")
            self.assertEqual(result["status"], "tool_error")
            self.assertEqual(result["errors"][0]["code"], "E_PROTOCOL")

    def test_authority_warning_is_pass_not_fail(self):
        payload = {"status": "pass", "errors": [{"severity": "warning", "message": "warning: dead code", "line": 3}]}
        cfg = {"authoritative": {"command": self._command(payload)}}
        with tempfile.TemporaryDirectory(dir=ROOT / ".test_tmp") as tmp:
            result = Toolchain(cfg, time.monotonic() + 10, tmp).compile("", "warning")
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["errors"][0]["code"], "W_DEAD_CODE")

    def test_authority_inconsistent_pass_rejected(self):
        for code, errors in [(1, []), (0, [{"severity": "error", "message": "error: syntax"}])]:
            cfg = {"authoritative": {"command": self._command({"status": "pass", "errors": errors}, code)}}
            with tempfile.TemporaryDirectory(dir=ROOT / ".test_tmp") as tmp:
                result = Toolchain(cfg, time.monotonic() + 10, tmp).compile("", "contradiction")
                self.assertEqual(result["status"], "tool_error")

    def test_fixture_never_provides_authoritative_evidence(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".test_tmp") as tmp:
            chain = Toolchain({}, time.monotonic() + 10, tmp, "fixture")
            good = chain.compile("PROGRAM P\nEND_PROGRAM", "good")
            bad = chain.compile("FIXTURE_COMPILE_FAIL", "bad")
            self.assertEqual(good["status"], "pass")
            self.assertFalse(good["authoritative_available"])
            self.assertEqual(bad["status"], "fail")
            self.assertEqual(good["evidence_kind"], "fixture")
            self.assertEqual(chain.test("FIXTURE_TEST_FAIL", "t")["passed"], 1)
            self.assertEqual(chain.verify("", "v")["status"], "skipped")

    def test_test_contract_has_identifiable_nonempty_cases(self):
        payload = {"status": "pass", "total": 0, "passed": 0, "passed_ids": [], "failures": []}
        cfg = {"test": {"command": self._command(payload)}}
        with tempfile.TemporaryDirectory(dir=ROOT / ".test_tmp") as tmp:
            chain = Toolchain(cfg, time.monotonic() + 10, tmp)
            self.assertEqual(chain.test("", "empty")["status"], "tool_error")
        payload = {"status": "fail", "total": 3, "passed": 2, "passed_ids": ["safe", "edge"], "failures": [{"case_id": "seq", "cycle": 12}]}
        cfg = {"test": {"command": self._command(payload)}}
        with tempfile.TemporaryDirectory(dir=ROOT / ".test_tmp") as tmp:
            result = Toolchain(cfg, time.monotonic() + 10, tmp).test("", "partial")
            self.assertEqual(result["passed_ids"], ["safe", "edge"])
            self.assertEqual(result["failures"][0]["cycle"], 12)

    def test_import_split_handles_comments_strings_and_types(self):
        text = "TYPE ST_A : STRUCT\n x : INT;\nEND_STRUCT\nEND_TYPE\nFUNCTION_BLOCK FB_X\nVAR_INPUT\n a : ST_A;\nEND_VAR\n(* END_FUNCTION_BLOCK fake (* nested *) *)\ns := 'END_VAR'; // comment\nEND_FUNCTION_BLOCK"
        bundle = split_source(text)
        self.assertEqual(bundle["name"], "FB_X")
        self.assertEqual(bundle["types"][0]["name"], "ST_A")
        self.assertIn("s := 'END_VAR'", bundle["implementation"])
        self.assertNotIn("s :=", bundle["declaration"])
        self.assertTrue(bundle["declaration"].startswith("FUNCTION_BLOCK FB_X"))
        self.assertNotIn("TYPE ST_A", bundle["declaration"])

    def test_import_refuses_multiple_pous_or_unparsed_content(self):
        for text in ["PROGRAM P\nEND_PROGRAM\nPROGRAM Q\nEND_PROGRAM", "not_a_pou", "PROGRAM P\nEND_PROGRAM\nignored_code"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    split_source(text)

    def test_all_member1_skeletons_split_without_dropping_types(self):
        from agent.src.parse import parse_task
        from agent.src.task_card import make_skeleton
        paths = sorted((ROOT / "data" / "tasks").glob("*.yaml"))
        self.assertEqual(len(paths), 34)
        for path in paths:
            with self.subTest(task=path.stem):
                skeleton = make_skeleton(parse_task(path, root=ROOT))
                bundle = split_source(skeleton)
                self.assertEqual(bundle["kind"], "FUNCTION_BLOCK")
                self.assertEqual(bundle["name"], "FB_" + path.stem)
                self.assertNotIn("END_TYPE", bundle["declaration"])


if __name__ == "__main__":
    unittest.main()
