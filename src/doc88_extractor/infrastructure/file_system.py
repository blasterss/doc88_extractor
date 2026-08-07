"""Операции с локальными путями, файлами и архивами."""

import os
import tarfile
import zipfile
from pathlib import Path


def ospath(path: str) -> str | Path:
    """Добавляет префикс длинного пути Windows, когда он необходим."""
    if os.name == "nt":
        full_path = Path(path)
        if len(str(full_path.absolute())) >= 260:
            return "\\\\?\\" + str(full_path.absolute())
        return full_path
    return path


def safe_filename(value: str) -> str:
    """Заменяет запрещённые в именах файлов символы."""
    replacements = str.maketrans(
        {
            "*": "＊",
            "|": "｜",
            ":": "：",
            "?": "？",
            "/": "／",
            "<": "＜",
            ">": "＞",
            '"': "＂",
            "\\": "＼",
        }
    )
    return value.translate(replacements)


def write_bytes(data: bytes, path: str) -> None:
    with open(ospath(path), "wb") as file:
        file.write(data)


def write_text(data: str, path: str) -> None:
    with open(ospath(path), "w", encoding="utf-8") as file:
        file.write(data)


def read_text(path: str) -> str:
    with open(ospath(path), encoding="utf-8") as file:
        return file.read()


def read_bytes(path: str) -> bytes:
    with open(ospath(path), "rb") as file:
        return file.read()


def extract_archive(source: str, destination: str) -> None:
    """Распаковывает ZIP или tar-архив."""
    if source.endswith(".zip"):
        with zipfile.ZipFile(source) as archive:
            archive.extractall(destination)
    elif source.endswith((".tar.gz", ".tgz")):
        with tarfile.open(source, "r:*") as archive:
            archive.extractall(path=destination)
    else:
        raise ValueError(f"Неподдерживаемый формат архива: {source}")
