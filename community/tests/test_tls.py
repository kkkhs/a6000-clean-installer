"""Frozen TLS regression coverage: synthetic loopback peers only, never USB."""
import ast
import importlib.util
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
if 'pmca' not in sys.modules:
    package = types.ModuleType('pmca')
    package.__path__ = [str(ROOT / 'pmca')]
    sys.modules['pmca'] = package

from pmca.marketserver.selftest import verify_local_tls, verify_python_aes
from tlslite.utils import python_aes


class FrozenTlsTests(unittest.TestCase):
    def test_python_aes_known_answer_vectors(self):
        self.assertTrue(verify_python_aes())

    def test_reproduces_pinned_dependency_without_caller_source(self):
        # Reproduce the released EXE failure without launching a camera or EXE.
        # tlslite-ng 0.8.2 inspects Python_AES's caller source for a deprecated
        # class alias. PyInstaller's bytecode-only mode gives it None instead.
        namespace = {'__name__': 'tlslite.utils.python_aes_frozen_probe',
                     '__package__': 'tlslite.utils'}
        source = Path(python_aes.__file__).read_text(encoding='utf-8')
        exec(compile(source, '<frozen-without-python-aes-source>', 'exec'), namespace)
        with self.assertRaisesRegex(TypeError, "'NoneType' object is not iterable"):
            namespace['new'](b'\x00' * 16, 2, b'\x00' * 16)

    def test_both_specs_retain_tls_source(self):
        for filename in ['pmca-a6000-offline.spec', 'pmca-a6000-online.spec']:
            with self.subTest(spec=filename):
                tree = ast.parse((ROOT / filename).read_text(encoding='utf-8'))
                analysis = [node for node in ast.walk(tree)
                            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                            and node.func.id == 'Analysis']
                self.assertEqual(len(analysis), 1)
                modes = [kw for kw in analysis[0].keywords if kw.arg == 'module_collection_mode']
                self.assertEqual(len(modes), 1)
                self.assertEqual(ast.literal_eval(modes[0].value), {'tlslite': 'pyz+py'})

    def test_real_local_tls_http_and_spk_round_trip(self):
        reports = verify_local_tls(ROOT / 'certs' / 'localtest.me.pem')
        self.assertEqual([report['version'] for report in reports], ['TLS 1.0', 'TLS 1.2'])
        for report in reports:
            self.assertEqual(report['cipher'], 'aes128')
            self.assertTrue(report['httpVerified'])
            self.assertTrue(report['spkRoundTripVerified'])
            self.assertFalse(report['cameraConnected'])


if __name__ == '__main__':
    unittest.main()
