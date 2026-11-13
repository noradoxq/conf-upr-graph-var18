from collections import deque

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class DependencyGraph:

    adjacency: dict[str, list[str]] = field(
        default_factory=dict
    )

    depths: dict[str, int] = field(
        default_factory=dict
    )

    root: str = ""

    def add_node(self, node: str) -> None:

        if node not in self.adjacency:
            self.adjacency[node] = []

    def add_edge(self, source: str, target: str) -> None:

        self.add_node(source)
        self.add_node(target)

        if target not in self.adjacency[source]:
            self.adjacency[source].append(target)

    def has_node(self, node: str) -> bool:

        return node in self.adjacency

    def get_dependencies(self, node: str) -> list[str]:

        return self.adjacency.get(node, [])

    def get_nodes(self) -> list[str]:

        return list(self.adjacency.keys())

    def get_edges(self) -> list[tuple[str, str]]:

        edges = []

        for source, targets in self.adjacency.items():
            for target in targets:
                edges.append((source, target))

        return edges


class GraphBuilder:

    def __init__(
        self,
        dependency_provider: Callable[[str], list[str]],
        max_depth: int = 5
    ):
        if max_depth < 0:
            raise ValueError(
                "Максимальная глубина не может быть отрицательной."
            )

        self.dependency_provider = dependency_provider
        self.max_depth = max_depth

    def build(self, root: str) -> DependencyGraph:

        graph = DependencyGraph(root=root)

        graph.add_node(root)
        graph.depths[root] = 0


        queue = deque()

        queue.append((root, 0))

        visited = {root}

        def bfs_recursive() -> None:


            if not queue:
                return

            current, depth = queue.popleft()

            if depth < self.max_depth:

                dependencies = self.dependency_provider(
                    current
                )

                for dependency in dependencies:

                    graph.add_edge(
                        current,
                        dependency
                    )

                    if dependency not in visited:

                        visited.add(dependency)

                        graph.depths[dependency] = depth + 1

                        queue.append(
                            (dependency, depth + 1)
                        )

            bfs_recursive()

        bfs_recursive()

        return graph