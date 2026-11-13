import unittest

from unittest.mock import patch
from xml.etree import ElementTree as ET

from dependency_visualizer.maven import (
    MavenRepository,
    MavenRepositoryError
)


class MavenTests(unittest.TestCase):

    def setUp(self):
        self.repository = MavenRepository(
            "https://repo.maven.apache.org/maven2"
        )

    def test_build_pom_url(self):
        url = self.repository._build_pom_url(
            "org.slf4j",
            "slf4j-api",
            "2.0.16"
        )

        expected = (
            "https://repo.maven.apache.org/maven2/"
            "org/slf4j/slf4j-api/2.0.16/"
            "slf4j-api-2.0.16.pom"
        )

        self.assertEqual(url, expected)

    def test_resolve_properties(self):
        properties = {
            "version": "1.5.0"
        }

        result = self.repository._resolve_properties(
            "${version}",
            properties
        )

        self.assertEqual(result, "1.5.0")

    def test_direct_dependencies(self):

        xml = """
        <project xmlns="http://maven.apache.org/POM/4.0.0">

            <modelVersion>4.0.0</modelVersion>

            <groupId>com.example</groupId>
            <artifactId>application</artifactId>
            <version>1.0</version>

            <dependencies>

                <dependency>
                    <groupId>org.example</groupId>
                    <artifactId>library-a</artifactId>
                    <version>1.2.0</version>
                </dependency>

                <dependency>
                    <groupId>org.example</groupId>
                    <artifactId>library-b</artifactId>
                    <version>2.0.0</version>
                    <scope>test</scope>
                </dependency>

            </dependencies>

        </project>
        """

        root = ET.fromstring(xml)

        with patch.object(
            self.repository,
            "_download_pom",
            return_value=root
        ):
            dependencies = self.repository.get_dependencies(
                "com.example:application",
                "1.0"
            )

        self.assertEqual(len(dependencies), 2)

        self.assertEqual(
            dependencies[0].artifact_id,
            "library-a"
        )

        self.assertEqual(
            dependencies[1].scope,
            "test"
        )

    def test_empty_dependencies(self):

        xml = """
        <project xmlns="http://maven.apache.org/POM/4.0.0">
            <modelVersion>4.0.0</modelVersion>
            <groupId>com.example</groupId>
            <artifactId>application</artifactId>
            <version>1.0</version>
        </project>
        """

        root = ET.fromstring(xml)

        with patch.object(
            self.repository,
            "_download_pom",
            return_value=root
        ):
            dependencies = self.repository.get_dependencies(
                "com.example:application",
                "1.0"
            )

        self.assertEqual(dependencies, [])

    def test_missing_dependency_version(self):

        xml = """
        <project xmlns="http://maven.apache.org/POM/4.0.0">

            <modelVersion>4.0.0</modelVersion>

            <groupId>com.example</groupId>
            <artifactId>application</artifactId>
            <version>1.0</version>

            <dependencies>
                <dependency>
                    <groupId>org.example</groupId>
                    <artifactId>library-a</artifactId>
                </dependency>
            </dependencies>

        </project>
        """

        root = ET.fromstring(xml)

        with patch.object(
            self.repository,
            "_download_pom",
            return_value=root
        ):
            with self.assertRaises(MavenRepositoryError):
                self.repository.get_dependencies(
                    "com.example:application",
                    "1.0"
                )


if __name__ == "__main__":
    unittest.main()