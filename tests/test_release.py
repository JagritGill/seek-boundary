from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.check_release import check

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def test_current_inventory(self):
        self.assertEqual(check(ROOT)["files"], 22)

    def mutate(self, action):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)/"release"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            action(root)
            with self.assertRaises((ValueError, SyntaxError)):
                check(root)

    def test_inventory_symlink_and_mode(self):
        self.mutate(lambda root: (root/"extra.txt").write_text("extra"))
        self.mutate(lambda root: (root/"README.md").unlink())
        self.mutate(lambda root: (root/"link").symlink_to(root/"README.md"))
        self.mutate(lambda root: (root/"README.md").chmod(0o755))

    def test_links_syntax_and_patterns(self):
        self.mutate(lambda root: (root/"README.md").write_text("[missing](absent.md)"))
        self.mutate(lambda root: (root/"seek_boundary/core.py").write_text("def x(:"))
        self.mutate(lambda root: (root/"README.md").write_text("AKIA" + "0" * 16))
        self.mutate(lambda root: (root/"README.md").write_text("/" + "Users" + "/fixture/data"))
        self.mutate(lambda root: (root/"README.md").write_bytes(bytes([27]) + b"[2J"))
