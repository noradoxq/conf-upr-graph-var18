import unittest

from dependency_visualizer.graph import GraphBuilder


class GraphTests(unittest.TestCase):

    def setUp(self):

        self.dependencies = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["E"],
            "D": ["F"],
            "E": ["F"],
            "F": []
        }

        def provider(package):
            return self.dependencies.get(package, [])

        self.provider = provider

    def test_basic_graph(self):

        builder = GraphBuilder(
            self.provider,
            max_depth=5
        )

        graph = builder.build("A")

        self.assertEqual(
            len(graph.get_nodes()),
            6
        )

        self.assertEqual(
            len(graph.get_edges()),
            6
        )

    def test_max_depth_zero(self):

        builder = GraphBuilder(
            self.provider,
            max_depth=0
        )

        graph = builder.build("A")

        self.assertEqual(
            graph.get_nodes(),
            ["A"]
        )

        self.assertEqual(
            graph.get_edges(),
            []
        )

    def test_max_depth_one(self):

        builder = GraphBuilder(
            self.provider,
            max_depth=1
        )

        graph = builder.build("A")

        self.assertEqual(
            set(graph.get_nodes()),
            {"A", "B", "C"}
        )

        self.assertEqual(
            len(graph.get_edges()),
            2
        )

    def test_max_depth_two(self):

        builder = GraphBuilder(
            self.provider,
            max_depth=2
        )

        graph = builder.build("A")

        self.assertEqual(
            set(graph.get_nodes()),
            {"A", "B", "C", "D", "E"}
        )

    def test_cycle(self):

        dependencies = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"]
        }

        builder = GraphBuilder(
            lambda package: dependencies.get(package, []),
            max_depth=10
        )

        graph = builder.build("A")

        self.assertEqual(
            len(graph.get_nodes()),
            3
        )

        self.assertEqual(
            len(graph.get_edges()),
            3
        )

    def test_shared_dependency(self):

        dependencies = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": []
        }

        builder = GraphBuilder(
            lambda package: dependencies.get(package, []),
            max_depth=5
        )

        graph = builder.build("A")

        self.assertEqual(
            len(graph.get_nodes()),
            4
        )

        self.assertIn(
            ("B", "D"),
            graph.get_edges()
        )

        self.assertIn(
            ("C", "D"),
            graph.get_edges()
        )

    def test_empty_dependencies(self):

        builder = GraphBuilder(
            lambda package: [],
            max_depth=5
        )

        graph = builder.build("A")

        self.assertEqual(
            graph.get_nodes(),
            ["A"]
        )

        self.assertEqual(
            graph.get_edges(),
            []
        )

    def test_invalid_depth(self):

        with self.assertRaises(ValueError):
            GraphBuilder(
                self.provider,
                max_depth=-1
            )


if __name__ == "__main__":
    unittest.main()