"""Установка и проверка платформенных утилит presse/svg2pdf."""

import os
import platform
import subprocess
import zipfile

from ..core.config import Config
from ..infrastructure.file_system import extract_archive
from ..infrastructure.http_client import download
from ..infrastructure.release_client import GitHubRelease
from ..presentation.console import wait_for_enter


class BinaryToolManager:
    """Управляет исполняемыми файлами из GitHub Releases."""

    def __init__(self, config: Config) -> None:
        self.config = config

    @staticmethod
    def asset_name(tool: str) -> str | None:
        system = platform.system()
        machine = platform.machine().lower()
        arm = "arm64" in machine or "aarch64" in machine
        if system == "Windows":
            target = "aarch64" if arm else "x86_64"
            return f"{tool}-{target}-pc-windows-msvc.zip"
        if system == "Darwin":
            target = "aarch64" if arm else "x86_64"
            return f"{tool}-{target}-apple-darwin.tar.gz"
        if system == "Linux":
            target = "aarch64-unknown-linux-musl" if arm else "x86_64-unknown-linux-gnu"
            return f"{tool}-{target}.tar.gz"
        return None

    @staticmethod
    def binary_name(tool: str) -> str:
        return f"{tool}.exe" if os.name == "nt" else f"./{tool}"

    def install(self, tool: str) -> bool:
        """Загружает подходящий архив и распаковывает его в рабочий каталог."""
        try:
            release = GitHubRelease(getattr(self.config, f"{tool}_repo"))
            asset = self.asset_name(tool)
            if not asset or asset not in release.releases:
                print(f"Для текущей платформы нет готовой сборки {tool}.")
                return False
            archive_url = self.config.proxy_url + release.releases[asset]
            print(f"Загрузка {tool}: {archive_url}")
            download(archive_url, asset)
            extract_archive(asset, ".")
            os.remove(asset)
            return True
        except (OSError, KeyError, zipfile.BadZipFile) as error:
            print(f"Не удалось установить {tool}: {error}")
            wait_for_enter()
            return False

    def ensure(self, tool: str) -> bool:
        """Проверяет запуск программы, устанавливая её при отсутствии."""
        binary = self.binary_name(tool)
        try:
            result = subprocess.run(
                [binary, "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                return True
            print(f"{tool} завершился с ошибкой: {result.stderr.strip()}")
            return False
        except FileNotFoundError:
            print(f"{tool} не установлен; выполняется загрузка.")
        except OSError as error:
            print(f"Не удалось запустить {tool}: {error}")
            return False
        return self.install(tool) and self.ensure(tool)
