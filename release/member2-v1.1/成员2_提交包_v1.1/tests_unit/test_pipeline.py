"""离线验证闭环关键契约；所有HTTP均被替换，不发送模型请求。"""

from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.src.generate import Provider
from agent.src.logging import FIELDS
from agent.src.repair import apply_patch, regresses
from agent.src.terminate import StopRun, check_limits, rank
import agent.run as runner


def candidate(status="pass", passed=2, ids=None, repairs=0, tokens=100):
    return {
        "compile": {"status": status},
        "test": {"status": "pass" if passed == 3 else "fail", "total": 3,
                 "passed": passed, "passed_ids": ids if ids is not None else [str(i) for i in range(passed)]},
        "repair_rounds": repairs, "token_count": tokens,
    }


class RepairSelectionTests(unittest.TestCase):
    def test_patch_requires_a_unique_existing_target(self):
        source = "FUNCTION_BLOCK FB_X\nVAR_OUTPUT\n x : BOOL;\nEND_VAR\nx := FALSE;\nEND_FUNCTION_BLOCK\n"
        fixed = apply_patch(source, json.dumps({"patches": [{"old": "x := FALSE;", "new": "x := TRUE;"}]}))
        self.assertIn("x := TRUE;", fixed)
        self.assertNotIn("x := FALSE;", fixed)
        for old in ("", "not present", "x"):
            with self.subTest(target=old), self.assertRaises(ValueError):
                apply_patch(source, json.dumps({"patches": [{"old": old, "new": "z"}]}))

    def test_full_file_replacement_is_rejected_even_for_short_program(self):
        source = "PROGRAM X\nx := FALSE;\nEND_PROGRAM\n"
        with self.assertRaises(ValueError):
            apply_patch(source, json.dumps({"patches": [{"old": source, "new": "PROGRAM Y\nEND_PROGRAM\n"}]}))

    def test_rollback_tracks_case_identity_not_only_count(self):
        previous = candidate(ids=["case_A", "case_B"])
        self.assertTrue(regresses(previous, candidate(ids=["case_A", "case_C"])))
        self.assertFalse(regresses(previous, candidate(passed=3, ids=["case_A", "case_B", "case_C"])))
        failed_compiler = candidate(status="fail", ids=["case_A", "case_B"])
        self.assertTrue(regresses(previous, failed_compiler))
        unavailable_tests = candidate(ids=["case_A", "case_B"])
        unavailable_tests["test"]["status"] = "tool_error"
        self.assertTrue(regresses(previous, unavailable_tests))

    def test_rank_filters_compilation_then_cases_repairs_and_tokens(self):
        self.assertGreater(rank(candidate(passed=0)), rank(candidate(status="fail", passed=3)))
        self.assertGreater(rank(candidate(passed=3, repairs=5, tokens=999)), rank(candidate(passed=2)))
        self.assertGreater(rank(candidate(repairs=1, tokens=999)), rank(candidate(repairs=2, tokens=1)))
        self.assertGreater(rank(candidate(tokens=1)), rank(candidate(tokens=2)))

    def test_limits_use_distinct_reasons(self):
        with self.assertRaises(StopRun) as timeout:
            check_limits(time.monotonic() - 1, 0, 100)
        self.assertEqual(timeout.exception.reason, "timeout")
        with self.assertRaises(StopRun) as budget:
            check_limits(time.monotonic() + 10, 100, 100)
        self.assertEqual(budget.exception.reason, "budget")


class ProviderContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT, prefix="tmp_provider_test_")
        self.directory = Path(self.temporary.name)
        self.env = mock.patch.dict(os.environ, {
            "DMXAPI_API_KEY": "unittest-placeholder-secret",
            "DMXAPI_BASE_URL": "https://unit.invalid/v1/",
        })
        self.env.start()
        self.config = {
            "base_url": "https://unit.invalid/v1/", "key_env": "DMXAPI_API_KEY",
            "request_timeout_s": 2, "send_temperature": True, "send_seed": True,
        }
        self.messages = [{"role": "user", "content": "Generate a PLC program."}]

    def tearDown(self):
        self.env.stop()
        self.temporary.cleanup()

    def provider(self, **kwargs):
        return Provider(self.config, "unit-model", 42, self.directory,
                        time.monotonic() + 10, **kwargs)

    def response(self, usage=None, content="PROGRAM X\nEND_PROGRAM"):
        result = {"choices": [{"message": {"content": content}}]}
        if usage is not None:
            result["usage"] = usage
        return io.BytesIO(json.dumps(result).encode("utf-8"))

    def test_dmx_url_headers_payload_and_no_secret_in_files(self):
        with mock.patch("urllib.request.urlopen", return_value=self.response({"prompt_tokens": 7, "completion_tokens": 3})) as http:
            provider = self.provider()
            provider.complete(self.messages, temperature=0.6)
        request = http.call_args.args[0]
        self.assertEqual(request.full_url, "https://unit.invalid/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer unittest-placeholder-secret")
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "unit-model")
        self.assertEqual(payload["messages"], self.messages)
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["temperature"], 0.6)
        self.assertEqual(payload["seed"], 42)
        self.assertEqual(provider.tokens_in, 7)
        self.assertEqual(provider.tokens_out, 3)
        saved = "\n".join(p.read_text(encoding="utf-8") for p in self.directory.rglob("*.json"))
        self.assertNotIn("unittest-placeholder-secret", saved)
        self.assertNotIn("Authorization", saved)

    def test_cached_request_is_not_resent_or_double_counted(self):
        with mock.patch("urllib.request.urlopen", return_value=self.response({"prompt_tokens": 7, "completion_tokens": 3})) as http:
            provider = self.provider()
            first = provider.complete(self.messages)
            second = provider.complete(self.messages)
        self.assertEqual(first, second)
        self.assertEqual(http.call_count, 1)
        self.assertEqual(provider.tokens_in, 7)
        self.assertEqual(provider.tokens_out, 3)

    def test_missing_usage_remains_explicitly_unknown(self):
        with mock.patch("urllib.request.urlopen", return_value=self.response()):
            provider = self.provider()
            provider.complete(self.messages)
        self.assertFalse(provider.usage_known)
        # 入口据usage_known输出JSON null，不能将内部0当作免费模型调用。
        exported = {"tokens_in": provider.tokens_in if provider.usage_known else None,
                    "tokens_out": provider.tokens_out if provider.usage_known else None}
        self.assertEqual(exported, {"tokens_in": None, "tokens_out": None})

    def test_null_usage_is_unknown_instead_of_crashing(self):
        with mock.patch("urllib.request.urlopen", return_value=self.response({"prompt_tokens": None, "completion_tokens": None})):
            provider = self.provider()
            provider.complete(self.messages)
        self.assertFalse(provider.usage_known)

    def test_pending_request_blocks_automatic_resend(self):
        with mock.patch("urllib.request.urlopen", side_effect=socket.timeout("simulated")) as http:
            with self.assertRaises(StopRun) as first:
                self.provider().complete(self.messages)
            self.assertEqual(first.exception.reason, "timeout")
            with self.assertRaises(StopRun) as second:
                self.provider().complete(self.messages)
            self.assertEqual(second.exception.reason, "uncertain_request")
        self.assertEqual(http.call_count, 1)
        self.assertEqual(len(list(self.directory.glob("*.pending.json"))), 1)

    def test_nonstring_content_is_a_response_error(self):
        with mock.patch("urllib.request.urlopen", return_value=self.response(content=None)):
            with self.assertRaises(StopRun) as result:
                self.provider().complete(self.messages)
        self.assertEqual(result.exception.reason, "api_response_invalid")


class EntrypointIntegrationTests(unittest.TestCase):
    """实跑父/子进程，检查续跑、参数隔离和父级硬超时。"""
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT, prefix="tmp_pipeline_test_")
        self.directory = Path(self.temporary.name)
        self.config = json.loads((ROOT / "agent/configs/default.yaml").read_text(encoding="utf-8"))
        self.config.update(candidates=1, max_repairs=1, concurrency=1, task_timeout_s=10)

    def tearDown(self):
        self.temporary.cleanup()

    def run_cli(self, config, out="out"):
        path = self.directory / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        command = [sys.executable, str(ROOT / "agent/run.py"), "--framework", "self", "--model", "fixture",
                   "--tasks", str(ROOT / "data/tasks/P01.yaml"), "--out", str(self.directory / out),
                   "--config", str(path), "--mode", "fixture"]
        return subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
                              capture_output=True, timeout=25)

    def test_result_22_fields_resume_skips_and_changed_config_is_rejected(self):
        first = self.run_cli(self.config)
        self.assertEqual(first.returncode, 0, first.stderr)
        run_dir = self.directory / "out/fixture/E3_P01_1_42"
        result_path = run_dir / "result.json"
        result_bytes = result_path.read_bytes()
        result = json.loads(result_bytes)
        self.assertEqual(set(result), set(FIELDS))
        self.assertEqual(result["final_status"], "passed")
        self.assertEqual(result["compile_stage"], "after_repair")
        metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
        self.assertFalse(metadata["eligible_for_experiments"])
        second = self.run_cli(self.config)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("SKIP E3_P01_1_42", second.stdout)
        self.assertEqual(result_bytes, result_path.read_bytes())
        lines = (self.directory / "out/fixture/runs.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        altered = copy.deepcopy(self.config)
        altered["candidates"] = 2
        third = self.run_cli(altered)
        self.assertEqual(third.returncode, 2)
        self.assertIn("run_id", third.stderr)
        self.assertEqual(result_bytes, result_path.read_bytes())

    def test_parent_timeout_writes_terminal_record_and_releases_lock(self):
        config = copy.deepcopy(self.config)
        config["task_timeout_s"] = 0.001
        started = time.monotonic()
        result = self.run_cli(config)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(time.monotonic() - started, 10)
        run_dir = self.directory / "out/fixture/E3_P01_1_42"
        record = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(record["final_status"], "abandoned:timeout")
        self.assertEqual(record["compile_status"], "timeout")
        self.assertFalse((run_dir / "running.lock").exists())
        metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["status"], "timeout")
        self.assertFalse(metadata["eligible_for_experiments"])

    def worker_job(self, config):
        directory = self.directory / "worker"
        directory.mkdir(exist_ok=True)
        return {
            "directory": str(directory), "config": config, "task": str(ROOT / "data/tasks/P01.yaml"),
            "mode": "fixture", "model": "fixture", "seed": 42, "retry_uncertain": False,
            "allow_degraded": False, "framework": "self", "run_id": "E3_P01_1_42", "setting_id": "E3",
            "repeat_idx": 1, "artifact_path": "fixture/E3_P01_1_42", "start_ts": "2026-10-31T00:00:00+00:00",
            "fingerprint": "unittest-worker",
        }

    def test_progressive_two_step_compile_repair_uses_latest_accepted_source(self):
        config = copy.deepcopy(self.config)
        config.update(max_repairs=5, stagnation_rounds=2)
        job = self.worker_job(config)
        source = "FUNCTION_BLOCK FB_P01\nbadOne := TRUE;\nbadTwo := TRUE;\nEND_FUNCTION_BLOCK\n"
        provider = mock.Mock(tokens_in=0, tokens_out=0, estimated_tokens=0, usage_known=True)
        provider.complete.side_effect = [source,
            json.dumps({"patches": [{"old": "badOne := TRUE;", "new": ""}]}),
            json.dumps({"patches": [{"old": "badTwo := TRUE;", "new": ""}]})]
        tools = mock.Mock()

        def compile_source(value, tag):
            errors = [{"code": "E_UNDECLARED", "severity": "error", "line": index + 1,
                       "message": "undeclared " + line, "raw": "undeclared " + line}
                      for index, line in enumerate(value.splitlines()) if "badOne" in line or "badTwo" in line]
            return {"status": "fail" if errors else "pass", "errors": errors,
                    "authoritative_available": False}

        tools.compile.side_effect = compile_source
        tools.test.return_value = {"status": "pass", "total": 3, "passed": 3,
                                   "passed_ids": ["one", "two", "three"], "failures": []}
        tools.verify.return_value = {"status": "skipped"}
        with mock.patch.object(runner, "Provider", return_value=provider), mock.patch.object(runner, "Toolchain", return_value=tools):
            runner.worker(job)
        record = json.loads((Path(job["directory"]) / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(record["final_status"], "passed")
        self.assertEqual(record["repair_rounds"], 2)
        final = (Path(job["directory"]) / "final.st").read_text(encoding="utf-8")
        self.assertNotIn("badOne", final)
        self.assertNotIn("badTwo", final)

    def test_unsupported_target_type_stops_before_paid_model_or_compile_calls(self):
        config=copy.deepcopy(self.config)
        config['tools']['unsupported_types']=['VARIANT']
        job=self.worker_job(config)
        job.update(task=str(ROOT/'data/tasks/P18.yaml'),mode='live',run_id='E3_P18_1_42')
        provider=mock.Mock(tokens_in=0,tokens_out=0,estimated_tokens=0,usage_known=True)
        tools=mock.Mock()
        with mock.patch.object(runner,'Provider',return_value=provider),mock.patch.object(runner,'Toolchain',return_value=tools):
            runner.worker(job)
        provider.complete.assert_not_called()
        tools.compile.assert_not_called()
        record=json.loads((Path(job['directory'])/'result.json').read_text(encoding='utf-8'))
        metadata=json.loads((Path(job['directory'])/'metadata.json').read_text(encoding='utf-8'))
        self.assertEqual(record['final_status'],'abandoned:unsupported_type')
        self.assertFalse(metadata['eligible_for_experiments'])
        self.assertEqual(metadata['environment_blockers'][0]['data_type'],'VARIANT')

    def test_total_budget_stops_before_a_new_model_call(self):
        config = copy.deepcopy(self.config)
        config["total_token_budget"] = 100
        job = self.worker_job(config)
        provider = mock.Mock(tokens_in=0, tokens_out=0, estimated_tokens=100, usage_known=True)
        with mock.patch.object(runner, "Provider", return_value=provider), mock.patch.object(runner, "Toolchain"):
            runner.worker(job)
        provider.complete.assert_not_called()
        record = json.loads((Path(job["directory"]) / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(record["final_status"], "abandoned:budget")

    def test_optional_verifier_exception_does_not_lose_terminal_record(self):
        job = self.worker_job(copy.deepcopy(self.config))
        source = "FUNCTION_BLOCK FB_P01\nEND_FUNCTION_BLOCK\n"
        provider = mock.Mock(tokens_in=0, tokens_out=0, estimated_tokens=0, usage_known=True)
        provider.complete.return_value = source
        tools = mock.Mock()
        tools.compile.return_value = {"status": "pass", "errors": [], "authoritative_available": False}
        tools.test.return_value = {"status": "pass", "total": 3, "passed": 3,
                                   "passed_ids": ["one", "two", "three"], "failures": []}
        tools.verify.side_effect = RuntimeError("simulated verifier crash")
        with mock.patch.object(runner, "Provider", return_value=provider), mock.patch.object(runner, "Toolchain", return_value=tools):
            runner.worker(job)
        directory = Path(job["directory"])
        record = json.loads((directory / "result.json").read_text(encoding="utf-8"))
        self.assertEqual(set(record), set(FIELDS))
        self.assertEqual(record["compile_status"], "pass")
        self.assertEqual(record["test_passed"], 3)
        self.assertIn(record["verify_status"], ("pass", "violated", "timeout", "skipped"))
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["tool_verify_status"], "tool_error")

    def test_repair_tool_fault_stops_without_replacing_last_model_artifact(self):
        for fault in ("tool_error", "timeout"):
            with self.subTest(status=fault):
                config = copy.deepcopy(self.config)
                config["max_repairs"] = 5
                job = self.worker_job(config)
                job["directory"] = str(self.directory / ("worker_" + fault))
                Path(job["directory"]).mkdir()
                source = "FUNCTION_BLOCK FB_P01\nbadOne := TRUE;\nEND_FUNCTION_BLOCK\n"
                provider = mock.Mock(tokens_in=0, tokens_out=0, estimated_tokens=0, usage_known=True)
                provider.complete.side_effect = [source,
                    json.dumps({"patches": [{"old": "badOne := TRUE;", "new": ""}]})]
                tools = mock.Mock()
                tools.compile.side_effect = [
                    {"status": "fail", "errors": [{"code": "E_UNDECLARED", "severity": "error", "line": 2,
                                                     "message": "undeclared badOne", "raw": "undeclared badOne"}],
                     "authoritative_available": False},
                    {"status": fault, "errors": [{"code": "E_TOOL", "severity": "error", "line": None,
                                                   "message": "simulated tool fault", "raw": "simulated tool fault"}],
                     "authoritative_available": False},
                ]
                with mock.patch.object(runner, "Provider", return_value=provider), mock.patch.object(runner, "Toolchain", return_value=tools):
                    runner.worker(job)
                directory = Path(job["directory"])
                record = json.loads((directory / "result.json").read_text(encoding="utf-8"))
                self.assertEqual(provider.complete.call_count, 2)
                self.assertEqual(record["final_status"], "abandoned:" + fault)
                self.assertEqual((directory / "final.st").read_text(encoding="utf-8"), source)


if __name__ == "__main__":
    unittest.main()
