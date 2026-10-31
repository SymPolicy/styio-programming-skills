"""Author-generated user-task smoke; requires explicit STYIO_BIN environment path."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

BINARY = os.environ.get('STYIO_BIN')
PROGRAMS = Path(__file__).resolve().parent / 'programs'

@unittest.skipUnless(BINARY, 'Set STYIO_BIN to run real user-program smoke')
class UserProgramSmoke(unittest.TestCase):
    def run_program(self, name, stdin, expected):
        binary = Path(BINARY).expanduser().resolve(strict=True)
        with tempfile.TemporaryDirectory(prefix='styio-user-smoke-') as tmp:
            result = subprocess.run([str(binary), '--file', str(PROGRAMS/(name+'.styio'))], input=stdin, capture_output=True, timeout=30, cwd=tmp)
        self.assertEqual(0, result.returncode, result.stderr.decode(errors='replace'))
        self.assertEqual(b'', result.stderr)
        self.assertEqual(expected, result.stdout)
    def test_triple_stdin(self):
        self.run_program('triple', b'-2\n0\n5\n', b'-6\n0\n15\n')
    def test_relay_two_types(self):
        self.run_program('relay', b'', b'7\nready\n')
    def test_zip_shorter_input(self):
        self.run_program('zip', b'', b'12\n24\n')

if __name__ == '__main__': unittest.main()
