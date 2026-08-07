
"""Модуль поиска дополнительных страниц документа.

Сканирует последовательные блоки данных на CDN и пытается обнаружить
дополнительные страницы, отсутствующие в предварительном просмотре.
"""

import gc
import json

import requests

from ..core.coder import encode, key2
from ..core.gen_cfg import GenConfig
from ..infrastructure.file_system import read_text, write_bytes, write_text
from ..infrastructure.http_client import get
from .compressor import Compressor


class GetMore:
    """Выполняет поиск и загрузку скрытых страниц, выходящих за пределы предпросмотра."""

    def __init__(
        self, cfg: GenConfig, level: int, filepath: str, page: int = 0
    ) -> None:
        self.cfg = cfg
        self.comp = Compressor()
        self.level = level
        self.chunk_size = 1024000
        self.header = bytearray()
        self.filepath = filepath
        self.newpageids: list[str] = []
        self.pagecount = page
        self.PH_data = get(self.cfg.ph(self.level).url).content
        self.progressfile = filepath + "progress.json"
        self.progress: dict = {"pk": [], "ph": []}
        self.save_progress("ph", self.level)
        self.PK_data = bytearray()
        self.ids: list[str] = []

    def read_progress(self) -> None:
        """Загружает информацию о прогрессе с диска."""
        self.progress = json.loads(read_text(self.progressfile))

    def save_progress(self, progress_type: str, page: int) -> None:
        """Сохраняет текущий прогресс на диск."""
        self.progress[progress_type].append(page)
        write_text(json.dumps(self.progress), self.progressfile)

    def start(self) -> list[str] | None:
        """Запускает процесс сканирования."""
        write_bytes(self.PH_data, f"{self.filepath}{self.cfg.ph(self.level).name}")
        if self._scan(self.level):
            return self._get_newpageids()
        self.PK_data.clear()
        self.PH_data = b""
        return None

    def _scan(self, scan_range: int = 0) -> bool:
        """Полностью загружает данные текущего уровня в память и ищет границы страниц."""
        print(f"level {self.level} start scanning...")
        headsize = int(self.cfg.headnums[self.level - 1])
        self.flags = [headsize]

        # Загружаем данные по частям: каждый запрос получает chunk_size байт.
        # Если сервер обрывает соединение при превышении лимита,
        # возникает исключение ChunkedEncodingError.
        self.PK_data = bytearray()
        offset = headsize
        page_num = 0

        while True:
            page_num += 1
            url = (
                self.cfg.ebt_host
                + "/getebt-"
                + encode(
                    f"{self.level}-{offset}-{self.chunk_size}-"
                    f"{self.cfg.p_swf}-{page_num}-{self.cfg.p_code}",
                    key2,
                )
                + ".ebt"
            )
            try:
                response = get(
                    url,
                    browser_impersonation=False,
                    content_type="",
                    stream=True,
                )
            except Exception:
                break

            if response.status_code != 200:
                break

            buf = bytearray()
            chunked_error = False

            try:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        buf.extend(chunk)
            except requests.exceptions.ChunkedEncodingError:
                chunked_error = True
                # Дочитываем оставшиеся байты по одному (если они есть).
                try:
                    while True:
                        b = response.raw.read(1)
                        if not b:
                            break
                        buf.extend(b)
                except Exception:
                    pass

            if not buf:
                break

            self.PK_data.extend(buf)

            # Если соединение не было оборвано и получено меньше chunk_size байт,
            # значит достигнут конец файла.
            if not chunked_error and len(buf) < self.chunk_size:
                break

            offset += self.chunk_size

        if len(self.PK_data) == 0:
            return False

        # Поиск границ страниц в памяти.
        self.header = bytearray()
        pos = 0
        page_start = 0
        status = False

        while pos < len(self.PK_data):
            b = self.PK_data[pos]

            if 32 <= pos <= 33:
                self.header.append(b)
            elif pos > 33:
                if b == self.header[0]:
                    status = True
                elif b == self.header[1]:
                    if status:
                        page_size = pos - 33 - page_start
                        if page_size < scan_range:
                            print(f"pass:{pos}-{page_size}")
                            status = False
                        else:
                            br = f"{headsize + page_start}-{page_size}"
                            page_data = self.PK_data[page_start:pos + 1]

                            if self._test_bytearray(page_data):
                                write_bytes(
                                    page_data,
                                    f"{self.filepath}getebt-"
                                    f"{encode(f'{self.level}-{headsize + page_start}-{page_size}-{self.cfg.p_swf}-{self.pagecount + len(self.ids) + 1}-{self.cfg.p_code}', key2)}.ebt",
                                )
                                self.save_progress(
                                    "pk",
                                    self.pagecount + len(self.ids) + 1,
                                )
                                print(f"found:{br}")
                                self.ids.append(br)
                                page_start = pos - 33
                            else:
                                print(f"zpass:{br}")
                                status = False
                    else:
                        status = False
                else:
                    status = False

            pos += 1

        # Обрабатываем оставшиеся данные.
        remaining_data = self.PK_data[page_start:]

        if remaining_data and self._test_bytearray(remaining_data):
            br = f"{headsize + page_start}-{len(remaining_data)}"
            write_bytes(
                remaining_data,
                f"{self.filepath}getebt-"
                f"{encode(f'{self.level}-{headsize + page_start}-{len(remaining_data)}-{self.cfg.p_swf}-{self.pagecount + len(self.ids) + 1}-{self.cfg.p_code}', key2)}.ebt",
            )
            self.save_progress(
                "pk",
                self.pagecount + len(self.ids) + 1,
            )
            self.ids.append(br)
            print(f"finish:{br}")
        else:
            print("Ошибка при обработке последней страницы. Возможно, изменился заголовок?")

        print(f"total page:{len(self.ids)}")
        self.PK_data.clear()
        self.PH_data = b""
        gc.collect()
        return True

    def _test_bytearray(self, data: bytearray) -> bool:
        """Проверяет, можно ли успешно распаковать указанные данные PK в SWF."""
        pk = self.comp._decompress_ebt_pk(data)
        ph = self.comp._decompress_ebt_ph(self.PH_data)

        if pk:
            write_bytes(
                self.comp._makeup(ph, bytearray(pk)),
                f"{self.filepath}swf/{self.pagecount + len(self.ids) + 1}.swf",
            )
            return True

        return False

    def _get_newpageids(self) -> list[str]:
        """Формирует список новых идентификаторов страниц по результатам сканирования."""
        pid = (
            f"{self.level}-"
            f"{self.cfg.pageids[0].split('-')[1]}-"
            f"{self.cfg.pageids[0].split('-')[2]}"
        )

        for i in range(len(self.ids)):
            self.newpageids.append(f"{pid}-{self.ids[i]}")

        self.ids.clear()
        return self.newpageids
