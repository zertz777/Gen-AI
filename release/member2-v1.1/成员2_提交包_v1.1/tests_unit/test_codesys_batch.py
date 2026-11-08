"""批量验收工具的离线契约测试；IDE进程和API均被替换，无真实编译声明。"""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BatchCompilerTests(unittest.TestCase):
    def setUp(self):
        self.driver = load("codesys_batch_driver_test", ROOT / "tools/check_codesys_compiler.py")
        self.native = load("codesys_batch_native_test", ROOT / "agent/scripts/codesys_compile_batch.py")
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT, prefix="tmp_batch_contract_")
        self.folder = Path(self.temporary.name)
        self.exe = self.folder / "CODESYS.exe"
        self.exe.write_bytes(b"unit-test-placeholder-never-executed")
        self.template = self.folder / "template.project"
        self.template.write_bytes(b"unit-test-placeholder-project")
        self.config = {"tools": {"authoritative": {"command": [sys.executable,
            "agent/scripts/codesys_bridge.py", "--source", "{source}", "--result", "{result}",
            "--task-card", "{task_card}", "--exe", str(self.exe), "--profile", "Unit Test Profile",
            "--template", str(self.template), "--application", "Application"]}}}
        self.settings = self.driver.parse_bridge_config(self.config)

    def tearDown(self):
        self.temporary.cleanup()

    def test_only_known_bridge_argv_and_exact_placeholders_are_accepted(self):
        self.assertEqual(self.settings["profile"], "Unit Test Profile")
        for mutation in ("other_script", "unknown_flag", "bad_placeholder", "duplicate"):
            with self.subTest(mutation=mutation):
                config = copy.deepcopy(self.config)
                args = config["tools"]["authoritative"]["command"]
                if mutation == "other_script":
                    args[1] = "arbitrary.py"
                elif mutation == "unknown_flag":
                    args.extend(["--run-anything", "x"])
                elif mutation == "bad_placeholder":
                    args[3] = "source.st"
                else:
                    args.extend(["--profile", "other"])
                with self.assertRaises(ValueError):
                    self.driver.parse_bridge_config(config)

    def test_preparation_clones_projects_and_hashes_actual_source_bytes(self):
        out = self.folder / "prepared"
        out.mkdir()
        cases, requests = self.driver.prepare_cases(out, self.settings, ROOT / "data/tasks/P08.yaml")
        self.assertEqual(len(cases), 7)
        self.assertEqual(len({request["project"] for request in requests}), 7)
        for case, request in zip(cases, requests):
            self.assertEqual(Path(request["project"]).read_bytes(), self.template.read_bytes())
            self.assertEqual(case["source_sha256"], self.driver.sha256(request["source"]))
        Path(requests[0]["project"]).write_bytes(b"changed clone")
        self.assertEqual(self.template.read_bytes(), b"unit-test-placeholder-project")
        skeleton = Path(requests[-1]["source"]).read_text(encoding="utf-8")
        self.assertIn("ARRAY[*] OF ST_AnalogChannel", skeleton)
        self.assertNotIn("channels[].", skeleton)

    def test_native_batch_continues_after_one_compile_exception(self):
        self.native.projects = object()
        self.native.system = object()
        requests = [{"case_id": name, "source_sha256": "test-sha", "result": str(self.folder / (name + ".json"))}
                    for name in ("broken", "good")]
        compile_request = mock.Mock(side_effect=[RuntimeError("one failed import"),
            {"status": "pass", "code_generated": True, "compiler": "CODESYS", "source_sha256": "test-sha", "errors": []}])
        with mock.patch.object(self.native.runpy, "run_path", return_value={"compile_request": compile_request}) as loader:
            result = self.native.execute_batch({"cases": requests, "summary": str(self.folder / "native.json")})
        self.assertEqual(compile_request.call_count, 2)
        self.assertEqual(result["status"], "completed")
        self.assertEqual([row["status"] for row in result["cases_completed"]], ["tool_error", "pass"])
        self.assertEqual(loader.call_args.kwargs["run_name"], "codesys_shared")
        first = json.loads(Path(requests[0]["result"]).read_text(encoding="utf-8"))
        self.assertEqual(first["status"], "tool_error")
        self.assertFalse(first["code_generated"])

    def test_missing_results_on_timeout_do_not_become_syntax_failures(self):
        case = {"case_id": "uncompleted", "expected": "fail"}
        request = {"result": str(self.folder / "missing.json")}
        row = self.driver.collect_case(case, request, {"status": "timeout"})
        self.assertEqual(row["status"], "timeout")
        self.assertEqual(row["expected_check"], "unavailable")
        self.assertFalse(row["evidence_available"])

    def test_pass_without_codegen_or_matching_hash_is_rejected(self):
        source = self.folder / "source.st"
        source.write_bytes(b"PROGRAM Test\nEND_PROGRAM\n")
        path = self.folder / "result.json"
        request = {"source": str(source), "result": str(path), "source_sha256": self.driver.sha256(source)}
        payload = {"status": "pass", "compiler": "CODESYS", "code_generated": False,
                   "source_sha256": request["source_sha256"], "errors": []}
        for version in (payload, {**payload, "code_generated": True, "source_sha256": "wrong"}):
            path.write_text(json.dumps(version), encoding="utf-8")
            row = self.driver.collect_case({"case_id": "good", "expected": "pass"}, request, {"status": "pass"})
            self.assertEqual(row["status"], "tool_error")
            self.assertFalse(row["evidence_available"])

    def test_dead_code_does_not_require_a_warning(self):
        source = self.folder / "source.st"
        source.write_bytes(b"PROGRAM Test\nEND_PROGRAM\n")
        path = self.folder / "result.json"
        checksum = self.driver.sha256(source)
        path.write_text(json.dumps({"status": "pass", "compiler": "CODESYS", "code_generated": True,
            "source_sha256": checksum, "errors": []}), encoding="utf-8")
        row = self.driver.collect_case({"case_id": "dead", "expected": "observe"},
            {"source": str(source), "result": str(path), "source_sha256": checksum}, {"status": "pass"})
        self.assertEqual(row["expected_check"], "matched")
        self.assertEqual(row["warning_count"], 0)
        # A localized message must retain the native bridge's classification.
        path.write_text(json.dumps({"status": "fail", "compiler": "CODESYS", "code_generated": False,
            "source_sha256": checksum, "errors": [{"code": "E_SYNTAX", "severity": "error",
                "raw": "应该采用'THEN'"}]}), encoding="utf-8")
        row = self.driver.collect_case({"case_id": "syntax", "expected": "fail"},
            {"source": str(source), "result": str(path), "source_sha256": checksum}, {"status": "pass"})
        self.assertEqual(row["diagnostic_codes"], ["E_SYNTAX"])

    def test_driver_starts_one_ide_and_preserves_only_case_results(self):
        config = self.folder / "config.json"
        config.write_text(json.dumps(self.config), encoding="utf-8")
        out = self.folder / "validation"

        def fake_process(command, timeout_s, cwd, env):
            batch = json.loads(Path(env["PLC_BATCH_REQUEST"]).read_text(encoding="utf-8"))
            for request in batch["cases"]:
                good = request["case_id"] in ("C00_good", "C05_dead_code")
                payload = {"status": "pass" if good else "fail", "compiler": "CODESYS",
                           "code_generated": good, "source_sha256": request["source_sha256"],
                           "elapsed_s": 0.01, "errors": [] if good else [{"severity": "error", "raw": "undeclared identifier"}]}
                Path(request["result"]).write_text(json.dumps(payload), encoding="utf-8")
            return {"status": "pass", "returncode": 0, "stdout": "", "stderr": "", "elapsed_s": 0.1}

        with mock.patch.object(self.driver, "run_process", side_effect=fake_process) as runner:
            summary = self.driver.validate(config, out)
        runner.assert_called_once()
        command = runner.call_args.args[0]
        self.assertEqual(command[0], str(self.exe))
        self.assertIn("--noUI", command)
        self.assertEqual(runner.call_args.kwargs["timeout_s"], 900)
        self.assertEqual(summary["acceptance_status"], "pass")
        self.assertEqual(summary["case_count"], 6)
        self.assertEqual(summary["model_calls"], 0)
        self.assertFalse(summary["functional_tests_run"])
        self.assertTrue((out / "summary.json").is_file())
        self.assertTrue((out / "cases.csv").is_file())
        self.assertTrue((out / "summary.md").is_file())
        with self.assertRaisesRegex(ValueError, "输出目录非空"):
            self.driver.validate(config, out)


if __name__ == "__main__":
    unittest.main()
