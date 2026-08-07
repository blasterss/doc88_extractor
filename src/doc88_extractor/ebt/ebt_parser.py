"""Разбор локальных имён EBT и XML-описания DOC88."""

import os
from typing import Any

from xmltodict import parse

from ..core.coder import decode, key2


def scan_directory(path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Возвращает отдельно заголовки PH и страницы PK из каталога."""
    if not os.path.isdir(path):
        raise ValueError("Указан некорректный каталог EBT.")

    headers: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    for name in os.listdir(path):
        if not name.endswith(".ebt"):
            continue
        fields = decode(name[7:-4], key2).split("-")
        file_path = os.path.join(path, name)
        if len(fields) == 6:
            headers.append(
                {
                    "level": int(fields[0]),
                    "headsize": int(fields[1]),
                    "chunk_size": int(fields[2]),
                    "p_swf": "-".join(fields[3:]),
                    "path": file_path,
                }
            )
        elif len(fields) == 8:
            pages.append(
                {
                    "level": int(fields[0]),
                    "headsize": int(fields[1]),
                    "chunk_size": int(fields[2]),
                    "p_swf": "-".join(fields[3:6]),
                    "page": int(fields[6]),
                    "p_code": fields[7],
                    "path": file_path,
                    "width": None,
                    "height": None,
                }
            )
    return headers, pages


def parse_xml(xml: str) -> tuple[list[dict], list[dict], str, str]:
    """Преобразует XML DOC88 в списки PH/PK и метаданные документа."""
    source = parse(xml)["doc"]
    if source["p_404"] == "1":
        raise FileNotFoundError("Документ не найден.")

    structure = source["p_struct"]
    raw_headers = structure["h"]
    raw_pages = structure["p"]
    if not isinstance(raw_headers, list):
        raw_headers = [raw_headers]
    if not isinstance(raw_pages, list):
        raw_pages = [raw_pages]

    headers = [
        {
            "level": header["@n"],
            "chunk_size": header["#text"],
            "p_swf": source["p_swf"],
        }
        for header in raw_headers
    ]
    pages = [
        {
            "level": page["e"],
            "width": page.get("w"),
            "height": page.get("h"),
            "headsize": page["p"],
            "chunk_size": page["l"],
            "p_swf": source["p_swf"],
            "page": page["@n"],
            "p_code": source["p_code"],
        }
        for page in raw_pages
    ]
    return headers, pages, source["p_name"], source["p_ebthost"]
