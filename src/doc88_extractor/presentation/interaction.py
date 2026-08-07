"""Интерактивный консольный интерфейс приложения."""

import os
import shutil

from ..app.workflow import ExtractionWorkflow
from ..compat.ebt_import import build_cfg, import_ebt
from ..core.config import Config
from ..core.gen_cfg import GenConfig
from ..infrastructure.file_system import ospath
from ..services.document_source import decode_main, load_from_url
from ..services.page_downloader import PageDownloader
from ..services.workspace import clean, initialize
from ..toolchain.updater import Update
from .console import confirm


class InputRouter:
    """Определяет тип пользовательского ввода и запускает сценарий."""

    def __init__(self, config: Config, workflow: ExtractionWorkflow) -> None:
        self.config = config
        self.workflow = workflow

    def handle_next(self) -> bool:
        """Читает и обрабатывает одну строку интерактивного ввода."""
        try:
            value = input("Введите данные: ").strip()
        except KeyboardInterrupt:
            return False
        if not value:
            return False
        if value.startswith("http"):
            return self._from_url(value)
        if value.isdigit():
            return self._from_url(f"https://www.doc88.com/p-{value}.html")
        if os.path.isdir(ospath(value)):
            return self._from_directory(value)
        if os.path.isfile(ospath(value)):
            print("Поддерживается каталог с исходными файлами EBT.")
            return False
        try:
            return self.workflow.extract(decode_main(value), scan_extra=self.config.get_more)
        except Exception:
            print("Некорректный ввод.")
            return False

    def _from_url(self, url: str) -> bool:
        try:
            source = load_from_url(url)
            return bool(source) and self.workflow.extract(source, scan_extra=self.config.get_more)
        except Exception as error:
            print(error)
            return False

    def _from_directory(self, path: str) -> bool:
        """Импортирует локальные EBT и передаёт их обычному сценарию."""
        try:
            headers, pages = import_ebt(path)
            if not headers or not pages:
                print("В каталоге не найдены полные данные PH/PK.")
                return False
            source = build_cfg(headers, pages)
            document = GenConfig(source)
            initialize(self.config, source)
            progress = PageDownloader(document, self.config)
            for header in headers:
                shutil.copy(ospath(header["path"]), ospath(self.config.dir_path))
                progress.save_progress("ph", header["level"])
            for page in pages:
                shutil.copy(ospath(page["path"]), ospath(self.config.dir_path))
                progress.save_progress("pk", page["page"])
            return self.workflow.extract(
                source,
                scan_extra=self.config.get_more,
                initialize_workspace=False,
            )
        except Exception as error:
            print(error)
            return False


def run(config: Config, *, debug: bool = False) -> int:
    """Запускает интерактивный цикл приложения."""
    print(f"DOC88 Extractor {config.version} ")
    print("Автор исходного проекта: Cuite_Piglin")
    print("Используйте программу только для материалов, к которым у вас есть законный доступ.\n")
    if not Update(config).check_tools():
        return 1

    print("Поддерживаются URL, ID документа, каталог EBT и данные m_main.")
    router = InputRouter(config, ExtractionWorkflow(config, debug=debug))
    while True:
        if router.handle_next():
            if config.clean:
                clean(config)
            if not confirm():
                return 0
