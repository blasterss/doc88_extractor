"""Создание и очистка рабочего каталога документа."""

import json
import os
import shutil

from ..core.config import Config
from ..infrastructure.file_system import ospath, write_bytes
from ..presentation.console import confirm


def initialize(config: Config, document: dict) -> None:
    """Вычисляет рабочие пути и создаёт каталоги текущего документа."""
    config.dir_path = config.o_dir_path + document["p_code"] + "/"
    config.swf_path = config.dir_path + config.o_swf_path
    config.svg_path = config.dir_path + config.o_svg_path
    config.pdf_path = config.dir_path + config.o_pdf_path

    try:
        os.makedirs(ospath(config.dir_path))
    except FileExistsError:
        if not confirm("exists"):
            raise RuntimeError("Операция отменена пользователем.") from None

    index_path = f"{config.dir_path}index.json"
    if not os.path.exists(ospath(index_path)):
        write_bytes(json.dumps(document).encode(), index_path)

    for path in (config.swf_path, config.svg_path, config.pdf_path):
        os.makedirs(ospath(path), exist_ok=True)


def clean(config: Config) -> None:
    """Удаляет временные файлы обработки, сохраняя индекс и итоговый PDF."""
    print("Очистка временных файлов...")
    for path in (config.swf_path, config.pdf_path, config.svg_path):
        shutil.rmtree(ospath(path), ignore_errors=True)
    for name in os.listdir(ospath(config.dir_path)):
        if name.endswith(".ebt") or name == "progress.json":
            os.remove(ospath(config.dir_path + name))
