"""Модуль разбора конфигурации страниц.

Преобразует исходный словарь конфигурации doc88 в структурированный объект
с информацией о страницах документа.
"""

from dataclasses import dataclass

from .coder import decode, encode, key2


@dataclass
class PageURL:
    """Имя файла страницы и URL для его загрузки."""

    name: str
    url: str


class GenConfig:
    """Конфигурация страниц документа.

    Содержит метаданные документа и предоставляет методы для формирования
    URL файлов PH и PK.
    """

    def __init__(self, config: dict) -> None:
        self.header_info: str = config["headerInfo"]
        self.p_swf: str = config["p_swf"]
        self.ebt_host: str = config["ebt_host"]
        self.p_code: str = config["p_code"]
        self.page_info: str = config["pageInfo"]
        self.p_name: str = config["p_name"]
        self.p_date: str = config["p_upload_date"]
        self.p_count_info: int = config["pageCount"]
        self.p_download: str = config["p_download"]
        self.p_doc_format: str = config["p_doc_format"]
        self.p_pagecount: str = config["p_pagecount"]

        self.pageids: list[str] = decode(self.page_info).split(",")
        self.p_count: int = len(self.pageids)
        self.headnums: list[str] = self.header_info.replace('"', "").split(",")

    def ph_nums(self) -> int:
        """Возвращает общее количество файлов PH."""
        return len(self.headnums)

    def ph_num(self, page: int) -> int:
        """Возвращает номер уровня PH, используемого указанной страницей."""
        pageid = self.pageids[page - 1].split("-")
        return int(pageid[0])

    def ph(self, level: int) -> PageURL:
        """Формирует URL файла PH для указанного уровня."""
        name = (
            "getebt-"
            + encode(
                f"{level}-0-{self.headnums[level - 1]}-{self.p_swf}",
                key2,
            )
            + ".ebt"
        )
        return PageURL(name=name, url=f"{self.ebt_host}/{name}")

    def pk(self, page: int) -> PageURL:
        """Формирует URL файла PK для указанной страницы."""
        pageid = self.pageids[page - 1].split("-")
        level_num = int(pageid[0])
        name = (
            "getebt-"
            + encode(
                f"{level_num}-{pageid[3]}-{pageid[4]}-{self.p_swf}-{page}-{self.p_code}",
                key2,
            )
            + ".ebt"
        )
        return PageURL(name=name, url=f"{self.ebt_host}/{name}")
