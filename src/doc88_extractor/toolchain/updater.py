"""Координатор проверки внешней цепочки инструментов."""

import os
import platform

from ..core.config import Config
from ..infrastructure.release_client import GitHubRelease
from ..presentation.console import confirm, wait_for_enter
from ..services.document_catalog import DocumentCatalog
from .binary_tools import BinaryToolManager
from .ffdec_manager import FFDecManager
from .java_runtime import JavaRuntime


class Update:
    """Согласует независимые менеджеры при запуске приложения."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.catalog = DocumentCatalog(config.o_dir_path)
        self.ffdec = FFDecManager(config)
        self.binaries = BinaryToolManager(config)

    def check_update(self) -> bool:
        """Сообщает о новом выпуске приложения, не изменяя файлы."""
        try:
            release = GitHubRelease("cmy2008/doc88_extractor")
            current = self.config.version
            if release.latest_version.lstrip("vV") > current:
                print(f"Доступна версия приложения {release.latest_version}.")
            return True
        except Exception as error:
            print(f"Не удалось проверить обновление приложения: {error}")
            return False

    def upgrade(self) -> None:
        """Мигрирует каталог документов и обновляет его индекс."""
        if self.config.version < "1.7":
            self.catalog.upgrade_legacy_layout()
        self.catalog.rebuild_index()
        self.config.version = self.config.version
        self.config.save()

    def check_tools(self) -> bool:
        """Проверяет Java, ffdec, presse и необязательный svg2pdf."""
        if not JavaRuntime.available():
            wait_for_enter()
            return False
        if not self.ffdec.ensure_current() or not self.ffdec.configure():
            print("ffdec отсутствует или не может быть настроен.")
            wait_for_enter()
            return False
        if self.config.check_update:
            self.check_update()
        self.upgrade()
        if not self.binaries.ensure("presse"):
            wait_for_enter()
            return False
        if self.config.swf2svg and not self.check_svg2pdf():
            self.config.swf2svg = False
            print("Преобразование через SVG отключено.")
        return True

    def check_svg2pdf(self) -> bool:
        """Проверяет необязательный конвертер SVG."""
        binary = self.binaries.binary_name("svg2pdf")
        if os.path.isfile(binary):
            return True
        if platform.system() not in {"Windows", "Linux", "Darwin"}:
            return False
        if not confirm("Установить необязательный svg2pdf? (Y/n): "):
            return False
        return self.binaries.install("svg2pdf")

    # Совместимые методы прежнего API.
    def get_ffdec_asset(self):
        return self.ffdec.release_asset()

    def download_ffdec(self) -> bool:
        return self.ffdec.install()

    def ffdec_update(self) -> bool:
        return self.ffdec.install()

    @staticmethod
    def check_java() -> bool:
        return JavaRuntime.available()

    def ffdec_configure(self) -> bool:
        return self.ffdec.configure()

    def check_ffdec_update(self) -> bool:
        return self.ffdec.ensure_current()

    def download_tool(self, tool_name: str) -> bool:
        return self.binaries.install(tool_name)

    def check_required_tool(self, tool_name: str) -> bool:
        return self.binaries.ensure(tool_name)
