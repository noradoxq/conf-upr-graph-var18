import sys

from dependency_visualizer.cli import parse_args
from dependency_visualizer.maven import (
    MavenRepository,
    MavenRepositoryError
)


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

    if args.test_mode:
        print(
            "\nОшибка: тестовый режим будет реализован "
            "на третьем этапе.",
            file=sys.stderr
        )
        sys.exit(1)

    print("\nПолучение зависимостей Maven...")

    try:
        repository = MavenRepository(
            args.repository
        )

        dependencies = repository.get_dependencies(
            args.package,
            args.version
        )

    except MavenRepositoryError as exc:
        print(
            f"\nОшибка получения зависимостей: {exc}",
            file=sys.stderr
        )
        sys.exit(1)

    print("\nПрямые зависимости:")

    if not dependencies:
        print("Зависимости отсутствуют.")
        return

    for number, dependency in enumerate(
        dependencies,
        start=1
    ):
        print(f"{number}. {dependency}")

    print(
        f"\nВсего прямых зависимостей: {len(dependencies)}"
    )


if __name__ == "__main__":
    main()