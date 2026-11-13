"""Получение прямых зависимостей Maven из POM-файлов."""

import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from typing import Optional


MAVEN_NAMESPACE = {
    "m": "http://maven.apache.org/POM/4.0.0"
}


class MavenRepositoryError(Exception):
    """Ошибка при загрузке или обработке Maven POM."""


@dataclass
class Dependency:
    """Информация о Maven-зависимости."""

    group_id: str
    artifact_id: str
    version: str
    scope: str = "compile"
    optional: bool = False

    def __str__(self) -> str:
        result = (
            f"{self.group_id}:{self.artifact_id}:{self.version}"
            f" [scope={self.scope}]"
        )

        if self.optional:
            result += " [optional]"

        return result


@dataclass
class MavenModel:
    """Модель Maven-проекта."""

    group_id: str
    artifact_id: str
    version: str
    properties: dict
    dependency_management: dict
    dependencies: list


class MavenRepository:
    """Клиент для получения POM-файлов из Maven-репозитория."""

    def __init__(self, repository_url: str):
        self.repository_url = repository_url.rstrip("/")
        self._cache = {}
        self._loading = set()

    def _build_pom_url(
        self,
        group_id: str,
        artifact_id: str,
        version: str
    ) -> str:
        """Формирует URL POM-файла."""

        group_path = group_id.replace(".", "/")

        return (
            f"{self.repository_url}/"
            f"{group_path}/"
            f"{artifact_id}/"
            f"{version}/"
            f"{artifact_id}-{version}.pom"
        )

    def _download_pom(
        self,
        group_id: str,
        artifact_id: str,
        version: str
    ) -> ET.Element:
        """Загружает и разбирает POM-файл."""

        url = self._build_pom_url(
            group_id,
            artifact_id,
            version
        )

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "DependencyVisualizer/0.1"}
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=20
            ) as response:
                content = response.read()

        except urllib.error.HTTPError as exc:
            raise MavenRepositoryError(
                f"HTTP-ошибка {exc.code} при загрузке {url}"
            ) from exc

        except urllib.error.URLError as exc:
            raise MavenRepositoryError(
                f"Не удалось подключиться к репозиторию: {exc.reason}"
            ) from exc

        except TimeoutError as exc:
            raise MavenRepositoryError(
                f"Превышено время ожидания: {url}"
            ) from exc

        try:
            return ET.fromstring(content)

        except ET.ParseError as exc:
            raise MavenRepositoryError(
                f"Некорректный XML в POM-файле: {url}"
            ) from exc

    @staticmethod
    def _get_text(
        element,
        tag: str
    ) -> Optional[str]:
        """Получает текст XML-элемента."""

        if element is None:
            return None

        child = element.find(
            f"m:{tag}",
            MAVEN_NAMESPACE
        )

        if child is None or child.text is None:
            return None

        return child.text.strip()

    @staticmethod
    def _resolve_properties(
        value: Optional[str],
        properties: dict
    ) -> Optional[str]:
        """Подставляет значения Maven-свойств."""

        if value is None:
            return None

        pattern = re.compile(r"\$\{([^}]+)\}")

        for _ in range(20):
            updated = pattern.sub(
                lambda match: str(
                    properties.get(
                        match.group(1),
                        match.group(0)
                    )
                ),
                value
            )

            if updated == value:
                break

            value = updated

        if pattern.search(value):
            raise MavenRepositoryError(
                f"Не удалось разрешить свойство Maven: {value}"
            )

        return value

    def _load_parent(self, root):
        """Загружает родительский POM."""

        parent = root.find(
            "m:parent",
            MAVEN_NAMESPACE
        )

        if parent is None:
            return None

        coordinates = (
            self._get_text(parent, "groupId"),
            self._get_text(parent, "artifactId"),
            self._get_text(parent, "version")
        )

        if not all(coordinates):
            raise MavenRepositoryError(
                "Некорректное описание родительского POM"
            )

        return self._load_model(*coordinates)

    def _resolve_coordinates(
        self,
        root,
        parent,
        coordinates
    ):
        """Определяет координаты Maven-проекта."""

        group_id = self._get_text(root, "groupId")
        artifact_id = self._get_text(root, "artifactId")
        version = self._get_text(root, "version")

        if parent:
            group_id = group_id or parent.group_id
            version = version or parent.version

        return (
            group_id or coordinates[0],
            artifact_id or coordinates[1],
            version or coordinates[2]
        )

    def _build_properties(
        self,
        root,
        parent,
        coordinates
    ):
        """Формирует набор Maven-свойств."""

        group_id, artifact_id, version = coordinates

        properties = {}

        if parent:
            properties.update(parent.properties)

        properties.update({
            "project.groupId": group_id,
            "pom.groupId": group_id,
            "project.artifactId": artifact_id,
            "pom.artifactId": artifact_id,
            "project.version": version,
            "pom.version": version,
            "parent.groupId": parent.group_id if parent else "",
            "parent.version": parent.version if parent else ""
        })

        element = root.find(
            "m:properties",
            MAVEN_NAMESPACE
        )

        if element is not None:
            for prop in element:
                if prop.text:
                    name = prop.tag.split("}")[-1]
                    properties[name] = prop.text.strip()

        for key in list(properties):
            properties[key] = self._resolve_properties(
                properties[key],
                properties
            )

        return properties

    def _build_management(
        self,
        root,
        parent,
        properties
    ):
        """Обрабатывает dependencyManagement."""

        management = {}

        if parent:
            management.update(
                parent.dependency_management
            )

        element = root.find(
            "m:dependencyManagement/m:dependencies",
            MAVEN_NAMESPACE
        )

        if element is None:
            return management

        for dependency in element.findall(
            "m:dependency",
            MAVEN_NAMESPACE
        ):
            group_id = self._get_text(
                dependency,
                "groupId"
            )

            artifact_id = self._get_text(
                dependency,
                "artifactId"
            )

            if not group_id or not artifact_id:
                continue

            group_id = self._resolve_properties(
                group_id,
                properties
            )

            artifact_id = self._resolve_properties(
                artifact_id,
                properties
            )

            dep_type = (
                self._get_text(dependency, "type") or "jar"
            )

            version = self._get_text(
                dependency,
                "version"
            )

            scope = self._get_text(
                dependency,
                "scope"
            )

            if version:
                version = self._resolve_properties(
                    version,
                    properties
                )

            management[
                (group_id, artifact_id, dep_type)
            ] = {
                "version": version,
                "scope": scope
            }

        return management

    def _parse_dependency(
        self,
        element,
        properties,
        management
    ):
        """Разбирает одну зависимость."""

        group_id = self._get_text(
            element,
            "groupId"
        )

        artifact_id = self._get_text(
            element,
            "artifactId"
        )

        if not group_id or not artifact_id:
            return None

        group_id = self._resolve_properties(
            group_id,
            properties
        )

        artifact_id = self._resolve_properties(
            artifact_id,
            properties
        )

        dep_type = (
            self._get_text(element, "type") or "jar"
        )

        version = self._get_text(
            element,
            "version"
        )

        scope = self._get_text(
            element,
            "scope"
        )

        managed = management.get(
            (group_id, artifact_id, dep_type),
            {}
        )

        version = version or managed.get("version")

        if not version:
            raise MavenRepositoryError(
                f"Не удалось определить версию зависимости "
                f"{group_id}:{artifact_id}"
            )

        version = self._resolve_properties(
            version,
            properties
        )

        scope = scope or managed.get("scope") or "compile"

        optional = (
            self._get_text(element, "optional") or "false"
        ).lower() == "true"

        return Dependency(
            group_id=group_id,
            artifact_id=artifact_id,
            version=version,
            scope=scope,
            optional=optional
        )

    def _build_dependencies(
        self,
        root,
        parent,
        properties,
        management
    ):
        """Получает прямые зависимости проекта."""

        dependencies = []

        if parent:
            dependencies.extend(parent.dependencies)

        element = root.find(
            "m:dependencies",
            MAVEN_NAMESPACE
        )

        if element is None:
            return dependencies

        for dependency_element in element.findall(
            "m:dependency",
            MAVEN_NAMESPACE
        ):
            dependency = self._parse_dependency(
                dependency_element,
                properties,
                management
            )

            if dependency:
                dependencies.append(dependency)

        return dependencies

    def _load_model(
        self,
        group_id,
        artifact_id,
        version
    ):
        """Загружает Maven-модель проекта."""

        coordinates = (
            group_id,
            artifact_id,
            version
        )

        if coordinates in self._cache:
            return self._cache[coordinates]

        if coordinates in self._loading:
            raise MavenRepositoryError(
                f"Обнаружен цикл родительских POM: {coordinates}"
            )

        self._loading.add(coordinates)

        try:
            root = self._download_pom(*coordinates)

            parent = self._load_parent(root)

            model_coordinates = self._resolve_coordinates(
                root,
                parent,
                coordinates
            )

            properties = self._build_properties(
                root,
                parent,
                model_coordinates
            )

            management = self._build_management(
                root,
                parent,
                properties
            )

            dependencies = self._build_dependencies(
                root,
                parent,
                properties,
                management
            )

            model = MavenModel(
                group_id=model_coordinates[0],
                artifact_id=model_coordinates[1],
                version=model_coordinates[2],
                properties=properties,
                dependency_management=management,
                dependencies=dependencies
            )

            self._cache[coordinates] = model

            return model

        finally:
            self._loading.discard(coordinates)

    def get_dependencies(
        self,
        package: str,
        version: str
    ) -> list[Dependency]:
        """Возвращает прямые зависимости Maven-пакета."""

        if ":" not in package:
            raise MavenRepositoryError(
                "Координаты пакета должны иметь формат GROUP:ARTIFACT"
            )

        group_id, artifact_id = package.split(":", 1)

        model = self._load_model(
            group_id,
            artifact_id,
            version
        )

        return model.dependencies