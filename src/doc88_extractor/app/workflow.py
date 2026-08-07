"""Прикладной сценарий извлечения одного документа."""

import gc
import json
import os
import time

from ..core.coder import encode
from ..core.config import Config
from ..core.gen_cfg import GenConfig
from ..ebt.get_more import GetMore
from ..infrastructure.file_system import ospath, read_text, write_bytes
from ..presentation.console import confirm
from ..services.conversion import convert
from ..services.page_downloader import PageDownloader
from ..services.workspace import initialize


class ExtractionWorkflow:
    """Оркестрирует получение страниц без деталей транспорта и конвертации."""

    def __init__(self, config: Config, *, debug: bool = False) -> None:
        self.config = config
        self.debug = debug

    def extract(
        self,
        source: dict,
        *,
        scan_extra: bool = False,
        initialize_workspace: bool = True,
    ) -> bool:
        """Извлекает один документ из уже полученной конфигурации."""
        document = self._load_document(source)
        self._print_metadata(document)

        if int(document.p_pagecount) != document.p_count:
            scan_extra = True
            print(f"Страниц в предпросмотре: {document.p_count_info}")
            print(f"Страниц доступно напрямую: {document.p_count}")
            print("Возможно наличие дополнительных страниц.")

        if not confirm("Начать извлечение? (Y/n): "):
            return False
        if initialize_workspace:
            initialize(self.config, source)

        try:
            scanned = scan_extra and self._scan_extra(document, source)
            if not scanned:
                PageDownloader(document, self.config).run()
            if not self.debug:
                gc.collect()
                convert(document, self.config)
            return True
        except Exception as error:
            print(error)
            return False

    def _load_document(self, source: dict) -> GenConfig:
        index_path = f"{self.config.o_dir_path}{source['p_code']}/index.json"
        if os.path.exists(ospath(index_path)):
            source = json.loads(read_text(index_path))
        return GenConfig(source)

    @staticmethod
    def _print_metadata(document: GenConfig) -> None:
        print(f"Название: {document.p_name}")
        print(f"ID: {document.p_code}")
        print(f"Дата загрузки: {document.p_date}")
        print(f"Страниц: {document.p_pagecount}")
        if document.p_download == "1":
            print("Документ бесплатный и может быть доступен для загрузки на сайте.")

    def _scan_extra(self, document: GenConfig, source: dict) -> bool:
        if not confirm("Искать дополнительные страницы сканированием? (Y/n): "):
            print("Используется обычный режим загрузки.")
            return False

        print("Поиск дополнительных страниц...")
        page_ids: list[str] = []
        document.p_count = 0
        for level in range(1, document.ph_nums() + 1):
            scanner = GetMore(
                document, level, self.config.dir_path, document.p_count
            )
            scanner.start()
            page_ids.extend(scanner.newpageids)
            document.p_count += len(scanner.newpageids)

        document.pageids = page_ids
        source["pageInfo"] = encode(",".join(page_ids))
        source["p_count"] = document.p_count
        write_bytes(
            json.dumps(source).encode(),
            self.config.dir_path + "index.json",
        )
        print(f"Найдено страниц: {document.p_count}")
        gc.collect()
        time.sleep(2)
        return True
