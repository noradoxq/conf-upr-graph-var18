import json
import tempfile
import unittest

from pathlib import Path

from dependency_visualizer.test_repository import (
    TestRepository,
    TestRepositoryError
)


class TestRepositoryTests(unittest.TestCase):

    def setUp(self):

        self.temp = tempfile.TemporaryDirectory()

        self.addCleanup(self.temp.cleanup)

        self.file_path = Path(
            self.temp.name
        ) / "repository.json"

    def create_repository(self, data):

        self.file_path.write_text(
            json.dumps(data),
            encoding="utf-8"
        )

        return TestRepository(
            str(self.file_path)
        )

    def test_load_repository(self):

        repository = self.create_repository({
            "A": ["B", "C"],
            "B": ["D"],
            "C": []
        })

        self.assertEqual(
            repository.get_dependencies("A"),
            ["B", "C"]
        )

    def test_empty_dependencies(self):

        repository = self.create_repository({
            "A": []
        })

        self.assertEqual(
            repository.get_dependencies("A"),
            []
        )

    def test_unknown_package(self):

        repository = self.create_repository({
            "A": ["B"]
        })

        self.assertEqual(
            repository.get_dependencies("C"),
            []
        )

    def test_invalid_package_name(self):

        self.file_path.write_text(
            json.dumps({
                "abc": ["B"]
            }),
            encoding="utf-8"
        )

        with self.assertRaises(TestRepositoryError):
            TestRepository(str(self.file_path))

    def test_invalid_dependency(self):

        self.file_path.write_text(
            json.dumps({
                "A": ["invalid-name"]
            }),
            encoding="utf-8"
        )

        with self.assertRaises(TestRepositoryError):
            TestRepository(str(self.file_path))

    def test_invalid_json(self):

        self.file_path.write_text(
            "{invalid json",
            encoding="utf-8"
        )

        with self.assertRaises(TestRepositoryError):
            TestRepository(str(self.file_path))


if __name__ == "__main__":
    unittest.main()