import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

PACKAGE_RE = re.compile(r"^[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+$")
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+\-]*$")


class ValidatingArgumentParser(argparse.ArgumentParser):

    def error(self, message: str) -> None:
        self.print_usage()
        self.exit(2, f"{self.prog}: ошибка: {message}\n")


def positive_or_zero(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("должно быть целым числом") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("значение не может быть отрицательным")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = ValidatingArgumentParser(
        prog="depviz",
        description="Прототип CLI для анализа зависимостей Maven-пакетов.",
    )
    parser.add_argument("--package", required=True, metavar="GROUP:ARTIFACT",
                        help="координаты Maven-пакета, например org.slf4j:slf4j-api")
    parser.add_argument("--repository", required=True, metavar="URL_OR_PATH",
                        help="URL Maven-репозитория или путь к файлу тестового репозитория")
    parser.add_argument("--test-mode", action="store_true",
                        help="считать --repository путём к локальному тестовому файлу")
    parser.add_argument("--version", required=True, help="версия анализируемого пакета")
    parser.add_argument("--output", default="dependencies.png", metavar="FILE.png",
                        help="имя PNG-файла (по умолчанию: dependencies.png)")
    parser.add_argument("--ascii-tree", action="store_true",
                        help="включить вывод зависимостей в виде ASCII-дерева")
    parser.add_argument("--max-depth", type=positive_or_zero, default=5, metavar="N",
                        help="максимальная глубина анализа, 0 означает только корневой пакет (по умолчанию: 5)")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not PACKAGE_RE.fullmatch(args.package):
        parser.error("--package должен иметь формат GROUP:ARTIFACT (например, org.slf4j:slf4j-api)")

    if not VERSION_RE.fullmatch(args.version):
        parser.error("--version содержит недопустимые символы или пустое значение")

    output = Path(args.output)
    if not args.output.strip():
        parser.error("--output не может быть пустым")
    if output.suffix.lower() != ".png":
        parser.error("--output должен иметь расширение .png")
    if not output.parent.exists() or not output.parent.is_dir():
        parser.error(f"каталог для --output не существует: {output.parent}")
    if output.exists() and output.is_dir():
        parser.error("--output указывает на каталог, а не на файл")

    if args.test_mode:
        repository_file = Path(args.repository).expanduser()
        if not repository_file.exists():
            parser.error(f"тестовый файл из --repository не найден: {repository_file}")
        if not repository_file.is_file():
            parser.error("--repository в тестовом режиме должен указывать на файл")
        args.repository = str(repository_file.resolve())
    else:
        parsed = urlparse(args.repository)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            parser.error("--repository должен быть корректным HTTP(S)-URL; для файла укажите --test-mode")

    args.output = str(output)
    return args
