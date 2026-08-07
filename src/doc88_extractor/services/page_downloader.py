"""Параллельная загрузка PH/PK и восстановление страниц SWF."""

import gc
import json
import os
from concurrent.futures import ThreadPoolExecutor

from ..core.config import Config
from ..core.gen_cfg import GenConfig
from ..ebt.compressor import make_swf
from ..infrastructure.file_system import ospath, read_text, write_text
from ..infrastructure.http_client import download
from ..infrastructure.logging_utils import write_log


class PageDownloader:
    """Загружает ресурсы документа и ведёт журнал прогресса."""

    def __init__(self, document: GenConfig, config: Config) -> None:
        self.document = document
        self.config = config
        self.downloaded = True
        self.progress_path = config.dir_path + "progress.json"
        self.progress = self._load_progress()

    def _load_progress(self) -> dict[str, list[int]]:
        if not os.path.isfile(ospath(self.progress_path)):
            return {"pk": [], "ph": []}
        try:
            return json.loads(read_text(self.progress_path))
        except json.JSONDecodeError:
            return {"pk": [], "ph": []}

    def save_progress(self, resource_type: str, number: int) -> None:
        """Фиксирует успешно загруженный ресурс."""
        self.progress[resource_type].append(number)
        write_text(json.dumps(self.progress), self.progress_path)

    def download_header(self, level: int) -> None:
        """Загружает PH указанного уровня."""
        resource = self.document.ph(level)
        print(f"Загрузка PH {level}:\n{resource.url}")
        if level in self.progress["ph"]:
            print("Используется кеш.")
            return
        try:
            download(resource.url, self.config.dir_path + resource.name)
            self.save_progress("ph", level)
        except Exception as error:
            write_log(f"Ошибка загрузки PH {level}: {error}")
            self.downloaded = False

    def download_page(self, page: int) -> None:
        """Загружает PK указанной страницы."""
        resource = self.document.pk(page)
        print(f"Загрузка страницы {page}:\n{resource.url}")
        if page in self.progress["pk"]:
            print("Используется кеш.")
            return
        try:
            download(resource.url, self.config.dir_path + resource.name)
            self.save_progress("pk", page)
        except Exception as error:
            write_log(f"Ошибка загрузки страницы {page}: {error}")
            self.downloaded = False

    def build_page(self, page: int) -> None:
        """Объединяет PH и PK в страницу SWF."""
        try:
            level = self.document.ph_num(page)
            make_swf(
                self.config.dir_path + self.document.ph(level).name,
                self.config.dir_path + self.document.pk(page).name,
                self.config.swf_path + f"{page}.swf",
            )
        except Exception as error:
            print(f"Не удалось распаковать страницу {page}; она пропущена.")
            write_log(str(error))
            self.document.p_count -= 1

    def run(self) -> None:
        """Выполняет три последовательные параллельные стадии загрузки."""
        workers = self.config.download_workers
        self._parallel(self.download_header, range(1, self.document.ph_nums() + 1), workers)
        self._parallel(self.download_page, range(1, self.document.p_count + 1), workers)
        if not self.downloaded:
            raise RuntimeError("Не все ресурсы документа удалось загрузить.")
        self._parallel(self.build_page, range(1, self.document.p_count + 1), workers)
        self.progress.clear()
        print(f"Загрузка завершена. Страниц: {self.document.p_count}.")

    @staticmethod
    def _parallel(action, items, workers: int) -> None:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for item in items:
                executor.submit(action, item)
        gc.collect()
