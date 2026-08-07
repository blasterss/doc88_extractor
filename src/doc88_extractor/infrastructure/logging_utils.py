"""Минимальный файловый журнал приложения."""

import time
from pathlib import Path


def write_log(message: str) -> None:
    """Добавляет сообщение в суточный файл журнала."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    destination = log_dir / f"{time.strftime('%Y-%m-%d', time.localtime())}.log"
    with destination.open("a", encoding="utf-8") as file:
        file.write(f"[{timestamp}]: {message}\n")
