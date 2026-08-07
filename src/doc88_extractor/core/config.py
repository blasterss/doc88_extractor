"""Чтение и запись конфигурации приложения."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Config:
    """Конфигурация приложения."""

    version: str = "2.2.1"
    ffdec_version: str = "version26.2.2"

    o_dir_path: str = "docs/"
    o_swf_path: str = "swf/"
    o_pdf_path: str = "pdf/"
    o_svg_path: str = "svg/"

    proxy_url: str = ""
    ffdec_repo: str = "cmy2008/jpexs-decompiler"
    svg2pdf_repo: str = "cmy2008/svg2pdf"
    presse_repo: str = "cmy2008/presse"

    check_update: bool = True
    swf2svg: bool = True
    svgfontface: bool = True
    fix_displayrect: bool = False
    clean: bool = True
    get_more: bool = False
    path_replace: bool = True

    download_workers: int = 10
    convert_workers: int = 5
    pdf_scale: float = 1.0

    dir_path: str = field(default="", init=False)
    swf_path: str = field(default="", init=False)
    pdf_path: str = field(default="", init=False)
    svg_path: str = field(default="", init=False)

    def save(self, config_path: str | Path = "config.json") -> None:
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self)

        for key in ("dir_path", "swf_path", "pdf_path", "svg_path"):
            data.pop(key, None)

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            file.write("\n")

    @classmethod
    def load(cls, config_path: str | Path = "config.json") -> Config:
        """Загрузить конфигурацию или создать файл по умолчанию."""
        path = Path(config_path)

        if not path.exists():
            config = cls()
            config.save(path)
            return config

        with path.open("r", encoding="utf-8") as file:
            raw_data: Any = json.load(file)

        if not isinstance(raw_data, dict):
            raise ValueError("Корневой элемент конфигурации должен быть JSON-объектом.")

        known_fields = {field.name for field in fields(cls)}

        # Игнорируем неизвестные параметры и используем значения
        # по умолчанию для отсутствующих параметров.
        config_data = {key: value for key, value in raw_data.items() if key in known_fields}

        return cls(**config_data)
