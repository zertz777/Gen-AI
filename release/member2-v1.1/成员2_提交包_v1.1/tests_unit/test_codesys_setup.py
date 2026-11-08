"""CODESYS启动边界回归；使用API替身，不把测试算作真实PLC编译。"""
from __future__ import annotations
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "agent/scripts"


def load_template_module():
    spec = importlib.util.spec_from_file_location("codesys_create_template_test", SCRIPTS / "codesys_create_template.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CodesysSourceHashTests(unittest.TestCase):
    def run_native(self, source, wanted_hash):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix="tmp_codesys_hash_") as tmp:
            folder = Path(tmp)
            path = folder / "source.st"
            path.write_bytes(source)
            result = folder / "result.json"
            request = folder / "request.json"
            request.write_text(json.dumps({"source": str(path), "source_sha256": wanted_hash,
                "project": str(folder / "dummy.project"), "application": "Application", "result": str(result)}), encoding="utf-8")
            projects = types.SimpleNamespace(open=mock.Mock(side_effect=RuntimeError("SOURCE_HASH_ACCEPTED")))
            with mock.patch.dict(os.environ, {"PLC_AGENT_REQUEST": str(request)}), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(SCRIPTS / "codesys_compile.py"), init_globals={"projects": projects}, run_name="__main__")
            return json.loads(result.read_text(encoding="utf-8")), projects.open

    def test_raw_byte_hash_accepts_crlf_and_bom(self):
        for ending, prefix in ((b"\n", b""), (b"\r\n", b""), (b"\r\n", b"\xef\xbb\xbf")):
            with self.subTest(ending=ending, bom=bool(prefix)):
                source = prefix + ending.join((b"FUNCTION_BLOCK FB_Test", b"END_FUNCTION_BLOCK", b""))
                result, opened = self.run_native(source, hashlib.sha256(source).hexdigest())
                self.assertIn("SOURCE_HASH_ACCEPTED", result["errors"][0]["message"])
                opened.assert_called_once()

    def test_tampered_raw_source_is_rejected_before_opening_project(self):
        source = b"FUNCTION_BLOCK FB_Test\r\nEND_FUNCTION_BLOCK\r\n"
        result, opened = self.run_native(source, hashlib.sha256(source + b"changed").hexdigest())
        self.assertEqual(result["status"], "tool_error")
        self.assertIn("checksum changed", result["errors"][0]["message"])
        opened.assert_not_called()


class CodesysTemplateContractTests(unittest.TestCase):
    def setUp(self):
        self.module = load_template_module()
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT, prefix="tmp_codesys_template_")
        self.folder = Path(self.temporary.name)
        # 测试专用标识，不对应任何真实设备；生产代码必须从实际仓库枚举。
        self.did = types.SimpleNamespace(type=7, id="test-device-id", version="test-version")
        self.description = types.SimpleNamespace(device_id=self.did,
            device_info=types.SimpleNamespace(name="Unit Test Device", vendor="Unit Test Vendor"))
        self.module.device_repository = types.SimpleNamespace(get_all_devices=mock.Mock(return_value=[self.description]))
        self.module.librarymanager = types.SimpleNamespace(get_all_libraries=mock.Mock(return_value=[]))

    def tearDown(self):
        self.temporary.cleanup()

    def test_enumeration_is_actual_repository_data_and_creates_no_project(self):
        self.module.projects = types.SimpleNamespace(primary=None, create=mock.Mock(), open=mock.Mock())
        result = self.module.create_template({"action": "enumerate"})
        self.assertEqual(result["devices"][0]["id"], "test-device-id")
        self.assertFalse(result["template_created"])
        self.module.projects.create.assert_not_called()
        self.module.projects.open.assert_not_called()
        self.module.device_repository.get_all_devices.assert_called_once_with(name="", source=None)

    def test_uninstalled_device_is_rejected_before_project_creation(self):
        self.module.projects = types.SimpleNamespace(primary=None, create=mock.Mock(), open=mock.Mock())
        with self.assertRaisesRegex(ValueError, "not installed"):
            self.module.create_template({"output": str(self.folder / "new.project"),
                "device": {"type": 7, "id": "missing", "version": "test-version"}})
        self.module.projects.create.assert_not_called()

    def test_device_only_does_not_invent_application_api(self):
        device = mock.Mock(is_device=True)
        device.get_name.return_value = "Device"
        device.get_device_identification.return_value = self.did
        project = mock.Mock()
        project.get_children.side_effect = lambda recursive=False: [device] if not recursive else []
        self.module.projects = types.SimpleNamespace(primary=None, create=mock.Mock(return_value=project))
        with self.assertRaisesRegex(ValueError, "Device did not create Application"):
            self.module.create_template({"output": str(self.folder / "new.project"),
                "device": {"type": 7, "id": "test-device-id", "version": "test-version"}})
        project.add.assert_called_once_with(name="Device", type=7, id="test-device-id", version="test-version")
        project.close.assert_called_once()
        project.create_application.assert_not_called()

    def test_clone_saves_to_new_path_and_rebuilds_before_claiming_ready(self):
        seed = self.folder / "standard.project"
        seed.write_bytes(b"unit-test-standard-project")
        output = self.folder / "agent.project"
        device = mock.Mock(is_device=True, is_application=False)
        device.get_name.return_value = "Device"
        device.get_device_identification.return_value = self.did
        application = mock.Mock(is_device=False, is_application=True)
        application.get_name.return_value = "Application"
        application.get_library_manager.return_value.get_libraries.return_value = ["Standard, test (System)"]
        program = mock.Mock(has_textual_implementation=True)
        application.find.return_value = [program, types.SimpleNamespace(has_textual_implementation=False)]
        program.textual_implementation.text = ""
        application.get_children.return_value = []
        task = application.create_task_configuration.return_value.create_task.return_value
        application.create_task_configuration.return_value.find.return_value = []
        task.find.return_value = []
        project = mock.Mock()
        project.get_children.side_effect = lambda recursive=False: [device, application] if recursive else [device]
        self.module.projects = types.SimpleNamespace(primary=None, open=mock.Mock(return_value=project))
        self.module.KindOfTask = types.SimpleNamespace(Cyclic=1)
        self.module.system = types.SimpleNamespace(get_message_categories=mock.Mock(return_value=[]), clear_messages=mock.Mock())
        result = self.module.create_template({"template": str(seed), "output": str(output)})
        self.assertTrue(result["template_ready"])
        self.assertEqual(result["mode"], "clone")
        project.save_as.assert_called_once_with(str(output))
        application.rebuild.assert_called_once()
        application.create_program.assert_not_called()
        task.pous.add.assert_called_once_with("PLC_PRG")
        project.close.assert_called_once()
        self.assertEqual(seed.read_bytes(), b"unit-test-standard-project")


if __name__ == "__main__":
    unittest.main()
