import sys

from dependency_visualizer.cli import parse_args

from dependency_visualizer.maven import (
    MavenRepository,
    MavenRepositoryError
)

from dependency_visualizer.test_repository import (
    TestRepository,
    TestRepositoryError
)

from dependency_visualizer.graph import GraphBuilder


def print_graph(graph) -> None:

    print("\nГраф зависимостей:")

    for package, dependencies in graph.adjacency.items():

        if dependencies:
            print(
                f"{package} -> {', '.join(dependencies)}"
            )
        else:
            print(f"{package} -> []")

    print(f"\nКоличество вершин: {len(graph.get_nodes())}")
    print(f"Количество рёбер: {len(graph.get_edges())}")


def main() -> None:

    args = parse_args()
    values = {
        "package": args.package,
        "repository": args.repository,
        "test_mode": args.test_mode,
        "version": args.version,
        "output": args.output,
        "ascii_tree": args.ascii_tree,
        "max_depth": args.max_depth,
    }

    print("Параметры запуска:")

    for key, value in values.items():
        print(f"{key} = {value}")

    print("\nПостроение графа зависимостей...")

    try:

        if args.test_mode:

            repository = TestRepository(
                args.repository
            )

            dependency_provider = (
                repository.get_dependencies
            )

            root = args.package

        else:


            repository = MavenRepository(
                args.repository
            )

            group_id, artifact_id = args.package.split(":", 1)

            root = (
                f"{group_id}:{artifact_id}:{args.version}"
            )

            def dependency_provider(package: str) -> list[str]:

                parts = package.split(":")

                if len(parts) != 3:
                    raise MavenRepositoryError(
                        f"Некорректные координаты пакета: {package}"
                    )

                group, artifact, version = parts

                dependencies = repository.get_dependencies(
                    f"{group}:{artifact}",
                    version
                )

                return [
                    (
                        f"{dependency.group_id}:"
                        f"{dependency.artifact_id}:"
                        f"{dependency.version}"
                    )
                    for dependency in dependencies
                ]


        builder = GraphBuilder(
            dependency_provider=dependency_provider,
            max_depth=args.max_depth
        )

        graph = builder.build(root)


        print_graph(graph)

    except (
        MavenRepositoryError,
        TestRepositoryError,
        RecursionError
    ) as exc:

        print(
            f"\nОшибка: {exc}",
            file=sys.stderr
        )

        sys.exit(1)


if __name__ == "__main__":
    main()