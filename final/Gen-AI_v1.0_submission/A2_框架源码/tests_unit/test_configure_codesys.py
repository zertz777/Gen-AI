"""本机配置与只读发现契约；测试文件不构成真实CODESYS工程或编译证据。"""
import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import configure_codesys as setup


class ConfigureCodesysTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / "work").mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        # rmdir只清理此测试创建的空目录；有其他任务文件时保持原样。
        try:
            (ROOT / "work").rmdir()
        except OSError:
            pass

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codesys_setup_", dir=ROOT / "work")
        self.root = Path(self.temp.name)
        self.exe = self.root / "installation with spaces" / "CODESYS.exe"
        self.exe.parent.mkdir()
        fake_exe = bytearray(128)
        fake_exe[:2] = b"MZ"
        fake_exe[60:64] = (64).to_bytes(4, "little")
        fake_exe[64:68] = b"PE\x00\x00"
        self.exe.write_bytes(fake_exe)
        self.template = self.root / "local" / "template.project"
        self.template.parent.mkdir()
        self.template.write_bytes(b"TEST_TEMPLATE_NOT_A_REAL_PROJECT")
        self.default = self.root / "agent/configs/default.yaml"
        self.default.parent.mkdir(parents=True)
        self.config = {"config_version": "1.0", "provider": {"key_env": "DMXAPI_API_KEY"},
                       "tools": {"fast": {"command": []},
                                 "authoritative": {"command": [], "timeout_s": 90},
                                 "test": {"command": []}}}
        self.default.write_text(json.dumps(self.config), encoding="utf-8")
        self.bridge = self.root / "agent/scripts/codesys_bridge.py"
        self.bridge.parent.mkdir(parents=True)
        self.bridge.write_text("# test bridge placeholder, not executed\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def configure(self, **kwargs):
        values = dict(exe=str(self.exe), profile="CODESYS V3.5 SP22", template=str(self.template), root=self.root)
        values.update(kwargs)
        return setup.configure(**values)

    def test_configuration_uses_relative_project_paths_and_preserves_default(self):
        before = self.default.read_bytes()
        result = self.configure()
        config = json.loads((self.root / result["config"]).read_text(encoding="utf-8"))
        argv = config["tools"]["authoritative"]["command"]
        self.assertEqual(argv[1], "agent/scripts/codesys_bridge.py")
        self.assertEqual(argv[argv.index("--exe") + 1], "installation with spaces/CODESYS.exe")
        self.assertEqual(argv[argv.index("--template") + 1], "local/template.project")
        self.assertEqual(argv[argv.index("--source") + 1], "{source}")
        self.assertEqual(argv[argv.index("--task-card") + 1], "{task_card}")
        self.assertEqual(config["tools"]["authoritative"]["timeout_s"], 90)
        self.assertEqual(self.default.read_bytes(), before)
        self.assertEqual(result["compile_status"], "not_run")

    def test_environment_records_hashes_and_does_not_claim_compile_or_profile_verified(self):
        self.configure()
        env = json.loads((self.root / "local/codesys_environment.json").read_text(encoding="utf-8"))
        self.assertEqual(env["codesys"]["sha256"], setup.sha256_file(self.exe))
        self.assertEqual(env["template"]["sha256"], setup.sha256_file(self.template))
        self.assertFalse(env["codesys"]["profile_verified_in_ide"])
        self.assertFalse(env["template"]["opened_in_codesys"])
        self.assertEqual(env["compile_status"], "not_run")
        self.assertFalse(env["network_access"])

    def test_credentials_in_environment_are_not_copied(self):
        with patch.dict("os.environ", {"DMXAPI_API_KEY": "private-do-not-copy", "OPENAI_API_KEY": "private-do-not-copy"}):
            self.configure()
        for file in (self.root / "local").glob("*.json"):
            self.assertNotIn("private-do-not-copy", file.read_text(encoding="utf-8"))
        self.assertNotIn("private-do-not-copy", (self.root / "local/codesys.local.yaml").read_text(encoding="utf-8"))

    def test_missing_file_rejected_before_any_output(self):
        with self.assertRaisesRegex(ValueError, "不存在"):
            self.configure(exe=str(self.root / "missing" / "CODESYS.exe"))
        self.assertFalse((self.root / "local/codesys_environment.json").exists())

    def test_placeholder_profile_and_template_rejected(self):
        for profile in ("REPLACE_WITH_INSTALLED_PROFILE", "<真实profile>", "待填写", ""):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                self.configure(profile=profile)
        with self.assertRaises(ValueError):
            self.configure(template="REPLACE_WITH_PROJECT_PATH.project")

    def test_installer_or_non_pe_rejected(self):
        installer = self.exe.with_name("CODESYS Installer.exe")
        installer.write_bytes(b"MZnot-the-ide")
        with self.assertRaisesRegex(ValueError, "Installer"):
            self.configure(exe=str(installer))
        self.exe.write_text("not executable", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PE"):
            self.configure()

    def test_empty_or_wrong_extension_project_rejected(self):
        self.template.write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "为空"):
            self.configure()
        other = self.template.with_suffix(".txt")
        other.write_bytes(b"not-a-project")
        with self.assertRaisesRegex(ValueError, ".project"):
            self.configure(template=str(other))

    def test_custom_local_output_supported_and_external_output_rejected(self):
        result = self.configure(out="local/profiles/custom.yaml")
        self.assertEqual(result["config"], "local/profiles/custom.yaml")
        self.assertTrue((self.root / result["config"]).is_file())
        with self.assertRaisesRegex(ValueError, "只能保存到"):
            self.configure(out="agent/configs/default.yaml")

    def test_additionalfolder_checks_real_directory(self):
        extra = self.root / "local/instance"
        extra.mkdir()
        self.configure(additionalfolder=str(extra))
        config = json.loads((self.root / "local/codesys.local.yaml").read_text(encoding="utf-8"))
        self.assertEqual(config["tools"]["authoritative"]["command"][-2:], ["--additionalfolder", "local/instance"])
        with self.assertRaisesRegex(ValueError, "目录不存在"):
            self.configure(additionalfolder=str(extra / "missing"))

    def test_probe_discovers_profiles_without_reading_content_or_writing_files(self):
        profiles = self.exe.parent / "Profiles"
        profiles.mkdir()
        profile = profiles / "CODESYS V3.5 SP22.profile"
        profile.write_text("not read as configuration", encoding="utf-8")
        result = setup.probe([self.exe.parent, self.root / "missing"], max_depth=2)
        self.assertEqual(len(result["executables"]), 1)
        self.assertEqual(result["profiles"][0]["possible_profile_name"], "CODESYS V3.5 SP22")
        self.assertFalse(result["profiles"][0]["profile_name_verified"])
        self.assertEqual(result["compile_status"], "not_run")
        self.assertFalse((self.root / "local/codesys_environment.json").exists())

    def test_probe_depth_limit(self):
        self.assertEqual(setup.probe([self.root], max_depth=0)["executables"], [])
        with self.assertRaises(ValueError):
            setup.probe([self.root], max_depth=100)

    def test_probe_recognizes_current_profile_xml(self):
        profile=self.exe.parent/'CODESYS V3.5 SP22 Patch 4.profile.xml'
        profile.write_text('<Profile/>',encoding='utf-8')
        result=setup.probe([self.exe.parent],max_depth=2)
        self.assertEqual(result['profiles'][0]['possible_profile_name'],'CODESYS V3.5 SP22 Patch 4')

    def test_check_queries_signature_but_does_not_require_it_or_run_ide(self):
        with patch.object(setup, "inspect_signature", return_value={"status": "Valid", "subject": "Example signer"}) as checked:
            self.configure(check=True)
        checked.assert_called_once_with(self.exe)
        env = json.loads((self.root / "local/codesys_environment.json").read_text(encoding="utf-8"))
        self.assertEqual(env["codesys"]["signature"]["status"], "Valid")
        self.assertEqual(env["compile_status"], "not_run")

    @unittest.skipUnless(sys.platform == "win32", "PowerShell命令编码仅用于Windows")
    def test_signature_path_is_data_not_powershell_code(self):
        malicious_name = Path("C:/test/$();quote'file.exe")
        result = subprocess.CompletedProcess([], 0, '{"status":"NotSigned"}', '')
        with patch.object(setup.shutil, "which", return_value="powershell.exe"), \
                patch.object(setup.subprocess, "run", return_value=result) as run:
            signature = setup.inspect_signature(malicious_name)
        self.assertEqual(signature["status"], "NotSigned")
        command = run.call_args.args[0]
        self.assertIn("-EncodedCommand", command)
        self.assertNotIn(str(malicious_name), command)
        decoded = base64.b64decode(command[-1]).decode("utf-16-le")
        self.assertNotIn(str(malicious_name), decoded)
        self.assertIn(base64.b64encode(str(malicious_name).encode("utf-8")).decode(), decoded)


if __name__ == "__main__":
    unittest.main()
