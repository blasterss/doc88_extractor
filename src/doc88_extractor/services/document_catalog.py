"""Миграция и построение локального каталога обработанных документов."""

import json
import os
import shutil


class DocumentCatalog:
    """Управляет индексами в корневом каталоге документов."""

    def __init__(self, root: str) -> None:
        self.root = os.path.normpath(root)

    def upgrade_legacy_layout(self) -> None:
        """Переносит старые каталоги под имена, равные ID документа."""
        if not os.path.isdir(self.root):
            return
        for name in os.listdir(self.root):
            source = os.path.join(self.root, name)
            index_path = os.path.join(source, "index.json")
            if not os.path.isdir(source) or not os.path.isfile(index_path):
                continue
            try:
                with open(index_path, encoding="utf-8") as file:
                    metadata = json.load(file)
                destination = os.path.join(self.root, metadata["p_code"])
                os.makedirs(destination, exist_ok=True)
                if os.path.normcase(source) == os.path.normcase(destination):
                    continue
                for item in os.listdir(source):
                    shutil.move(
                        os.path.join(source, item),
                        os.path.join(destination, item),
                    )
                shutil.rmtree(source)
            except Exception as error:
                print(f"Не удалось перенести каталог {source}: {error}")

    def rebuild_index(self) -> None:
        """Пересоздаёт сводный индекс документов."""
        os.makedirs(self.root, exist_ok=True)
        index: dict[str, str] = {}
        for name in os.listdir(self.root):
            metadata_path = os.path.join(self.root, name, "index.json")
            if not os.path.isfile(metadata_path):
                continue
            try:
                with open(metadata_path, encoding="utf-8") as file:
                    metadata = json.load(file)
                index[metadata["p_code"]] = metadata["p_name"]
            except Exception as error:
                print(f"Не удалось прочитать индекс {metadata_path}: {error}")
        with open(
            os.path.join(self.root, "indexs.json"), "w", encoding="utf-8"
        ) as file:
            json.dump(index, file, ensure_ascii=False, indent=2)
