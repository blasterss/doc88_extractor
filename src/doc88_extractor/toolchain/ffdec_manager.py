"""Установка, обновление и настройка JPEXS FFDec."""

import os
import re
import shutil
import subprocess
import zipfile

from ..core.config import Config
from ..infrastructure.file_system import extract_archive
from ..infrastructure.http_client import download
from ..infrastructure.logging_utils import write_log
from ..infrastructure.release_client import GitHubRelease
from ..presentation.console import confirm


class FFDecManager:
    """Управляет единственной локальной установкой ffdec."""

    directory = "ffdec"
    jar_path = "ffdec/ffdec.jar"

    def __init__(self, config: Config) -> None:
        self.config = config

    def release_asset(self) -> tuple[GitHubRelease, str | None]:
        release = GitHubRelease(self.config.ffdec_repo)
        version = release.latest_version.lstrip("vV")
        desired = f"ffdec_{version}.zip"
        if desired in release.releases:
            return release, desired
        candidates = [
            name for name in release.releases
            if re.fullmatch(r"ffdec_\d+\.\d+\.\d+\.zip", name)
        ]
        candidates.sort(
            key=lambda name: tuple(
                int(part) for part in name.removeprefix("ffdec_").removesuffix(".zip").split(".")
            ),
            reverse=True,
        )
        return release, candidates[0] if candidates else None

    def install(self) -> bool:
        """Загружает и распаковывает FFDec."""
        try:
            release, asset = self.release_asset()
            if not asset:
                print("В выпуске не найден архив ffdec.")
                return False
            if os.path.isdir(self.directory):
                if not confirm("Каталог ffdec уже существует. Пересоздать? (Y/n): "):
                    return False
                shutil.rmtree(self.directory)
            os.makedirs(self.directory)
            archive = f"{self.directory}/ffdec.zip"
            download(self.config.proxy_url + release.releases[asset], archive)
            extract_archive(archive, self.directory)
            os.remove(archive)
            return os.path.isfile(self.jar_path)
        except (OSError, KeyError, zipfile.BadZipFile) as error:
            print(f"Не удалось установить ffdec: {error}")
            return False

    def ensure_current(self) -> bool:
        """Проверяет наличие и при необходимости обновляет FFDec."""
        try:
            release, asset = self.release_asset()
            missing = not os.path.isfile(self.jar_path)
            outdated = release.latest_version != self.config.ffdec_version
            if missing or (outdated and self.config.check_update):
                label = asset or release.latest_version
                if not missing and not confirm(
                    f"Доступна новая версия ffdec ({label}). Обновить? (Y/n): "
                ):
                    return True
                if not self.install():
                    return False
                self.config.ffdec_version = release.latest_version
                self.config.save()
            return os.path.isfile(self.jar_path)
        except Exception as error:
            print(f"Не удалось проверить ffdec: {error}")
            return os.path.isfile(self.jar_path)

    def configure(self) -> bool:
        """Устанавливает параметры экспорта FFDec."""
        font_face = "true" if self.config.svgfontface else "false"
        try:
            subprocess.run(
                [
                    "java", "-jar", self.jar_path, "-config",
                    f"textExportExportFontFace={font_face},useMinimumStrokeWidth1Px=false",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except (OSError, subprocess.CalledProcessError) as error:
            write_log(f"Ошибка настройки ffdec: {error}")
            return False
