
from dependency_visualizer.cli import parse_args


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


if __name__ == "__main__":
    main()
