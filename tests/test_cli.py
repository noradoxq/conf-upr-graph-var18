import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dependency_visualizer.cli import parse_args

class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo_file = Path(self.temp.name) / "repo.json"
        self.repo_file.write_text("{}", encoding="utf-8")

    def test_valid_remote_configuration(self):
        args = parse_args([
            "--package", "org.slf4j:slf4j-api",
            "--repository", "https://repo.maven.apache.org/maven2",
            "--version", "2.0.16",
        ])
        self.assertEqual(args.package, "org.slf4j:slf4j-api")
        self.assertEqual(args.max_depth, 5)
        self.assertFalse(args.test_mode)

    def test_valid_test_configuration(self):
        args = parse_args([
            "--package", "A:B", "--repository", str(self.repo_file),
            "--test-mode", "--version", "1.0", "--max-depth", "0",
        ])
        self.assertTrue(args.test_mode)
        self.assertEqual(args.max_depth, 0)

    def test_invalid_package(self):
        with self.assertRaises(SystemExit):
            parse_args(["--package", "bad-coordinate", "--repository", "https://example.org", "--version", "1"])

    def test_invalid_repository_url(self):
        with self.assertRaises(SystemExit):
            parse_args(["--package", "g:a", "--repository", "not-a-url", "--version", "1"])

    def test_missing_test_repository_file(self):
        with self.assertRaises(SystemExit):
            parse_args(["--package", "A:B", "--repository", str(Path(self.temp.name) / "missing.json"), "--test-mode", "--version", "1"])

    def test_invalid_version(self):
        with self.assertRaises(SystemExit):
            parse_args(["--package", "g:a", "--repository", "https://example.org", "--version", "bad version"])

    def test_invalid_output_extension(self):
        with self.assertRaises(SystemExit):
            parse_args(["--package", "g:a", "--repository", "https://example.org", "--version", "1", "--output", "graph.svg"])

    def test_invalid_depth(self):
        with self.assertRaises(SystemExit):
            parse_args(["--package", "g:a", "--repository", "https://example.org", "--version", "1", "--max-depth", "-1"])


if __name__ == "__main__":
    unittest.main()
