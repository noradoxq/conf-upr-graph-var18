import json
import re

from pathlib import Path


PACKAGE_RE = re.compile(r"^[A-Z]+$")


class TestRepositoryError(Exception):
    pass


class TestRepository:

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.dependencies = {}

        self._load()

    def _validate_package(self, package, dependencies):

        if not isinstance(package, str):
            raise TestRepositoryError(
                "Имя пакета должно быть строкой."
            )

        if not PACKAGE_RE.fullmatch(package):
            raise TestRepositoryError(
                f"Некорректное имя пакета: {package}. "
                "Используйте заглавные латинские буквы."
            )

        if not isinstance(dependencies, list):
            raise TestRepositoryError(
                f"Зависимости пакета {package} должны быть списком."
            )

        for dependency in dependencies:
            if not isinstance(dependency, str):
                raise TestRepositoryError(
                    f"Некорректная зависимость пакета {package}."
                )

            if not PACKAGE_RE.fullmatch(dependency):
                raise TestRepositoryError(
                    f"Некорректное имя зависимости: {dependency}."
                )


def _load(self) -> None:
    """Загружает зависимости из JSON-файла."""

    try:
        with self.file_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as exc:
        raise TestRepositoryError(
            f"Некорректный JSON: {exc}"
        ) from exc

    except OSError as exc:
        raise TestRepositoryError(
            f"Не удалось прочитать файл: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise TestRepositoryError(
            "Корнем JSON должен быть объект с пакетами."
        )

    for package, dependencies in data.items():
        self._validate_package(package, dependencies)

        self.dependencies[package] = list(
            dict.fromkeys(dependencies)
        )

    def get_dependencies(self, package: str) -> list[str]:

        if not PACKAGE_RE.fullmatch(package):
            raise TestRepositoryError(
                f"Некорректное имя пакета: {package}"
            )

        return self.dependencies.get(package, [])