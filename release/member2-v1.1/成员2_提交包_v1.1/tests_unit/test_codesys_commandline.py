import unittest
from agent.src.tools import process_command

class CodesysCommandlineTests(unittest.TestCase):
    def test_quotes_follow_equal_sign_for_native_windows_parser(self):
        command=['C:/CODESYS/Common/CODESYS.exe','--profile=CODESYS V3.5 SP22 Patch 4',
                 '--runscript=D:/My Project/run.py','--noUI']
        result=process_command(command,windows=True)
        self.assertIn('--profile="CODESYS V3.5 SP22 Patch 4"',result)
        self.assertIn('--runscript="D:/My Project/run.py"',result)
        self.assertTrue(result.endswith('--noUI'))

    def test_other_executables_keep_normal_argv(self):
        command=['python','--message=a b']
        self.assertEqual(process_command(command,windows=True),command)

    def test_embedded_quote_is_rejected_without_using_a_shell(self):
        with self.assertRaises(ValueError):
            process_command(['C:/CODESYS.exe','--profile=bad"name'],windows=True)

if __name__=='__main__':unittest.main()
