"""CODESYS 脚本的 fake API 契约测试；不代表真实引擎编译通过。"""
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "agent" / "scripts" / "codesys_compile.py"


class TextDocument:
    def __init__(self):
        self.text = ""

    def replace(self, new_text):
        self.text = new_text


class Object:
    def __init__(self):
        self.textual_declaration = TextDocument()
        self.textual_implementation = TextDocument()


class Message:
    def __init__(self, severity, text, position_text="", number=1234, prefix="C"):
        self.severity, self.text, self.position_text = severity, text, position_text
        self.number, self.prefix = number, prefix


class FakeSystem:
    def __init__(self):
        self.messages = []

    def get_message_categories(self, active):
        return ["Build"]

    def clear_messages(self, category):
        self.messages = []

    def get_message_objects(self, category):
        return list(self.messages)


class FakeApplication:
    def __init__(self, system, build_messages=None, generate_messages=None, generate_exception=False):
        self.system = system
        self.build_messages, self.generate_messages = build_messages or [], generate_messages or []
        self.generate_exception = generate_exception
        self.calls, self.objects = [], {}

    def find(self, name, recursive):
        return []

    def create_function_block(self, name):
        self.objects[name] = Object()
        return self.objects[name]

    def create_program(self, name):
        return self.create_function_block(name)

    def create_function(self, name, return_type):
        return self.create_function_block(name)

    def create_dut(self, name):
        return self.create_function_block(name)

    def rebuild(self):
        self.calls.append("rebuild")
        self.system.messages.extend(self.build_messages)

    def generate_code(self):
        self.calls.append("generate_code")
        self.system.messages.extend(self.generate_messages)
        if self.generate_exception:
            raise RuntimeError("目标生成异常")


class FakeProject:
    def __init__(self, application):
        self.application, self.saved, self.closed = application, False, False

    def find(self, name, recursive):
        return [self.application] if name == "Application" else []

    def save(self):
        self.saved = True

    def close(self):
        self.closed = True


class FakeProjects:
    def __init__(self, project):
        self.project, self.opens = project, 0

    def open(self, path):
        self.opens += 1
        return self.project


class CodesysCompileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_root = ROOT / ".test_tmp_codesys"
        cls.temp_root.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp_root.rmdir()

    def setup_api(self, folder, **kwargs):
        system = FakeSystem()
        app = FakeApplication(system, **kwargs)
        project = FakeProject(app)
        projects = FakeProjects(project)
        source = Path(folder) / "source.st"
        # BOM + CRLF + 中文保证校验沿用原始字节，而非归一化后的文本。
        raw = b"\xef\xbb\xbf" + "FUNCTION_BLOCK FB_P01\r\nVAR_OUTPUT\r\n  Motor : BOOL;\r\nEND_VAR\r\n(* 中文 *)\r\nMotor := FALSE;\r\nEND_FUNCTION_BLOCK\r\n".encode("utf-8")
        source.write_bytes(raw)
        request = {"source": str(source), "project": str(Path(folder) / "template.project"),
                   "application": "Application", "result": str(Path(folder) / "result.json"),
                   "source_sha256": hashlib.sha256(raw).hexdigest()}
        namespace = runpy.run_path(str(SCRIPT), init_globals={"projects": projects, "system": system},
                                  run_name="codesys_compile_test")
        return namespace, request, projects, project, app

    def test_success_requires_rebuild_and_target_codegen(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            ns, request, _, project, app = self.setup_api(folder)
            result = ns["compile_request"](request)
            self.assertEqual(app.calls, ["rebuild", "generate_code"])
            self.assertEqual(result["status"], "pass")
            self.assertTrue(result["code_generated"])
            self.assertEqual(result["stages"]["build"]["status"], "pass")
            self.assertEqual(result["stages"]["generate"]["status"], "pass")
            self.assertTrue(app.objects["FB_P01"].textual_declaration.text.startswith("{attribute 'linkalways'}\n"))
            self.assertTrue(project.saved and project.closed)

    def test_codegen_error_never_counts_as_compile_pass(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            diagnostic = Message("Error", "目标代码生成失败", "Line 7 (Impl)")
            ns, request, _, project, app = self.setup_api(folder, generate_messages=[diagnostic])
            result = ns["compile_request"](request)
            self.assertEqual(app.calls, ["rebuild", "generate_code"])
            self.assertEqual(result["stages"]["build"]["status"], "pass")
            self.assertEqual(result["stages"]["generate"]["status"], "fail")
            self.assertEqual(result["status"], "fail")
            self.assertFalse(result["code_generated"])
            self.assertIn("生成失败", result["errors"][0]["raw"])
            self.assertTrue(project.closed)

    def test_failed_build_skips_codegen_and_records_why(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            ns, request, _, _, app = self.setup_api(folder, build_messages=[Message("Error", "Syntax error")])
            result = ns["compile_request"](request)
            self.assertEqual(app.calls, ["rebuild"])
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["stages"]["generate"]["status"], "skipped")
            self.assertEqual(result["stages"]["generate"]["reason"], "build_fail")

    def test_stage_snapshots_do_not_duplicate_prior_diagnostics(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            ns, request, _, _, _ = self.setup_api(folder,
                build_messages=[Message("Warning", "build warning")],
                generate_messages=[Message("Warning", "codegen warning")])
            result = ns["compile_request"](request)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(len(result["messages"]), 2)
            self.assertEqual(result["stages"]["generate"]["messages"][0]["raw"], "codegen warning")
            self.assertTrue(all(e["severity"] == "warning" for e in result["errors"]))

    def test_codegen_exception_is_tool_error_and_closes_project(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            ns, request, _, project, app = self.setup_api(folder, generate_exception=True)
            result = ns["compile_request"](request)
            self.assertEqual(app.calls, ["rebuild", "generate_code"])
            self.assertEqual(result["status"], "tool_error")
            self.assertEqual(result["stages"]["generate"]["status"], "tool_error")
            self.assertFalse(result["code_generated"])
            self.assertTrue(project.closed)

    def test_positions_retained_but_not_guessed_as_source_lines(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            diag = Message("Error", "line 99: Unknown identifier", "Line 3 (Impl)")
            ns, request, _, _, _ = self.setup_api(folder, generate_messages=[diag])
            result = ns["compile_request"](request)
            self.assertIsNone(result["errors"][0]["line"])
            self.assertEqual(result["messages"][0]["position_text"], "Line 3 (Impl)")
            self.assertEqual(result["source_line_mapping"]["status"], "known_object_partitions_calibrated")
            self.assertEqual(result["messages"][0]["native_number"], 1234)

    def test_calibrated_chinese_positions_map_only_the_known_object(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            ns, _, _, _, _ = self.setup_api(folder)
            mapping={'imported_text_spans':[
                dict(object_name='FB_Test',part='declaration',source_start_line=1,source_end_line=4,imported_prefix_lines=1),
                dict(object_name='FB_Test',part='implementation',source_start_line=5,source_end_line=6,imported_prefix_lines=0)]}
            locate=ns['diagnostic_source_line']
            self.assertEqual(locate(mapping,'FB_Test','4行 (Decl)'),3)
            self.assertEqual(locate(mapping,'FB_Test','行1,列1 (Impl)'),5)
            self.assertIsNone(locate(mapping,'PLC_PRG','行1,列1 (Impl)'))
            self.assertIsNone(locate(mapping,'FB_Test','行99,列1 (Impl)'))

    def test_checksum_mismatch_prevents_project_open(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            ns, request, projects, _, _ = self.setup_api(folder)
            request["source_sha256"] = "not-the-checksum"
            with self.assertRaises(ValueError):
                ns["compile_request"](request)
            self.assertEqual(projects.opens, 0)

    def test_main_writes_structured_codegen_evidence(self):
        with tempfile.TemporaryDirectory(dir=self.temp_root) as folder:
            _, request, projects, _, app = self.setup_api(folder)
            request_path = Path(folder) / "request.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            with patch.dict(os.environ, {"PLC_AGENT_REQUEST": str(request_path)}), redirect_stdout(io.StringIO()):
                runpy.run_path(str(SCRIPT), init_globals={"projects": projects, "system": app.system},
                               run_name="__main__")
            result = json.loads(Path(request["result"]).read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "pass")
            self.assertTrue(result["code_generated"])
            self.assertIn("generate", result["stages"])


if __name__ == "__main__":
    unittest.main()
