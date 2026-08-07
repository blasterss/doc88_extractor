
"""Чтение и запись конфигурации приложения."""

import json
import os
from typing import Any


class Config:
    """Менеджер конфигурации приложения.

    Автоматически загружает настройки из файла config.json.
    Если файл отсутствует, создаёт его с конфигурацией по умолчанию.
    """

    def __init__(self, config_path: str = "config.json") -> None:
        self.default_config: dict[str, Any] = {
            "version": "2.2",
            "ffdec_version": "version26.2.2",
            "o_dir_path": "docs/",
            "o_swf_path": "swf/",
            "o_pdf_path": "pdf/",
            "o_svg_path": "svg/",
            "proxy_url": "https://github.chenc.dev/",
            "ffdec_repo": "cmy2008/jpexs-decompiler",
            "svg2pdf_repo": "cmy2008/svg2pdf",
            "presse_repo": "cmy2008/presse",
            "check_update": True,
            "swf2svg": False,
            "svgfontface": False,
            "fix_displayrect": False,
            "clean": True,
            "get_more": False,
            "path_replace": True,
            "download_workers": 10,
            "convert_workers": 5,
            "pdf_scale": 1.0,
        }
        self.config_path = config_path
        # Пути, используемые только во время выполнения (не сохраняются в конфигурации)
        self.dir_path = ""
        self.swf_path = ""
        self.pdf_path = ""
        self.svg_path = ""

        if not os.path.exists(config_path):
            self._gen_default()
        self.load()

    def load(self) -> None:
        """Загружает конфигурацию из JSON-файла, подставляя значения по умолчанию для отсутствующих параметров."""
        with open(self.config_path, encoding="utf-8") as f:
            config_data: dict = json.load(f)

        # Заполняем отсутствующие параметры значениями по умолчанию
        for key, default_val in self.default_config.items():
            setattr(self, key, config_data.get(key, default_val))

    def _gen_default(self) -> None:
        """Создаёт файл конфигурации со значениями по умолчанию."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.default_config, f, indent=4)

    def reload(self) -> None:
        """Повторно загружает конфигурацию из файла."""
        self.load()

    def save(self) -> None:
        """Сохраняет текущую конфигурацию в JSON-файл."""
        config_data = {key: getattr(self, key) for key in self.default_config}
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
