import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / 'styio-programming'
spec = importlib.util.spec_from_file_location('styio_verify', PKG/'scripts/verify.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class VerifyTests(unittest.TestCase):
    def test_package_static(self):
        _, manifest, files = v.load_package()
        self.assertEqual(11, len(manifest['cases']))
        self.assertEqual(11, len(files))
    def test_bad_paths(self):
        for path in ('../x', '/x', 'x/../y', 'C:/x', 'x\\y', 'x//y', './x', ''):
            with self.subTest(path=path), self.assertRaises(ValueError):
                v.relative(path)
    def test_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'skill'; shutil.copytree(PKG, root)
            (root/'fixtures/upstream/example/hello_world.styio').write_text('wrong')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                v.load_package(root)
    def test_unknown_syntax_snippet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'skill'; shutil.copytree(PKG, root)
            with (root/'references/idioms.md').open('a') as f:
                f.write('\n```styio\nfictional_function()\n```\n')
            with self.assertRaisesRegex(ValueError, 'unverified'):
                v.load_package(root)
    def test_broken_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'skill'; shutil.copytree(PKG, root)
            with (root/'references/idioms.md').open('a') as f:
                f.write('\n[missing](missing.md)\n')
            with self.assertRaisesRegex(ValueError, 'broken'):
                v.load_package(root)
    def test_duplicate_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'skill'; shutil.copytree(PKG, root)
            path=root/'fixtures/cases.json'; data=json.loads(path.read_text()); data['cases'].append(data['cases'][0]); path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                v.load_package(root)
    def test_source_pin_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'skill'; shutil.copytree(PKG, root)
            path=root/'compatibility.json'; data=json.loads(path.read_text()); data['language']['commit']='0'*40; path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'pins disagree'):
                v.load_package(root)
    def test_negative_crash_is_not_rejection(self):
        case={'expect_exit':4,'expect_failure':True}; files={'stderr_source':b'diagnostic'}
        with tempfile.TemporaryDirectory() as tmp:
            for code in (-11, 139, 0):
                self.assertTrue(v.judge(case, files, subprocess.CompletedProcess([], code, b'', b'diagnostic'), Path(tmp)))
    def test_negative_requires_all_fragments(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(v.judge({'expect_exit':4,'expect_failure':True},{'stderr_source':b'first\nsecond\n'}, subprocess.CompletedProcess([],4,b'',b'first'),Path(tmp)))
    def test_stdout_is_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(v.judge({'expect_exit':0},{'stdout_source':b'20\n'}, subprocess.CompletedProcess([],0,b'20',b''),Path(tmp)))
    def test_static_cli_runtime_not_run(self):
        process=subprocess.run([sys.executable,str(PKG/'scripts/verify.py'),'--json'],capture_output=True,text=True)
        self.assertEqual(0, process.returncode)
        report=json.loads(process.stdout)
        self.assertEqual('not_run',report['runtime_status'])
        self.assertTrue(all(c['status']=='not_run' for c in report['cases']))
    def test_cli_usage_json(self):
        process=subprocess.run([sys.executable,str(PKG/'scripts/verify.py'),'--unknown'],capture_output=True,text=True)
        self.assertEqual(2, process.returncode)
        self.assertEqual('not_run',json.loads(process.stdout)['runtime_status'])

if __name__ == '__main__': unittest.main()
