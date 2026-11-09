import unittest
from agent.src.tools import _normalized_json_errors,normalize_errors

class NativeDiagnosticsTests(unittest.TestCase):
    def test_generic_bridge_errors_are_classified_without_guessing_lines(self):
        expected = [('Unknown identifier Motor', 'E_UNDECLARED'),
                    ("Cannot convert type 'BOOL' to type 'INT'", 'E_TYPE'),
                    ('Library missing: VendorMotion', 'E_LIBRARY'),
                    ("Syntax error: expected ';'", 'E_SYNTAX')]
        for message, code in expected:
            with self.subTest(code=code):
                result = _normalized_json_errors([dict(code='E_COMPILE',severity='error',
                    line=None,message=message,raw=message)])[0]
                self.assertEqual(result['code'],code)
                self.assertIsNone(result['line'])
                self.assertEqual(result['raw'],message)

    def test_dead_code_stays_a_warning(self):
        result = _normalized_json_errors([dict(code='W_COMPILE',severity='warning',
            line=None,message='Unreachable code',raw='Unreachable code')])[0]
        self.assertEqual(result['code'],'W_DEAD_CODE')
        self.assertEqual(result['severity'],'warning')

    def test_matiec_source_range_uses_actual_start_line(self):
        result=normalize_errors("source.st:5-1..5-17: error: Incompatible data types for ':=' operation.")
        self.assertEqual(result[0]['line'],5)
        self.assertEqual(result[0]['code'],'E_TYPE')

    def test_matiec_summary_is_not_a_second_error(self):
        rows=normalize_errors('source.st:5-1..5-17: error: Type mismatch\n1 error(s) found. Bailing out!')
        self.assertEqual(len(rows),1)

if __name__=='__main__':
    unittest.main()
