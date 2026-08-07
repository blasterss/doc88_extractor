"""Совместимый фасад прикладного API.

Новый код должен импортировать функции из специализированных модулей.
"""

from ..app.workflow import ExtractionWorkflow
from ..core.config import Config
from ..presentation.interaction import InputRouter as Mode
from ..presentation.interaction import run as _run
from ..services.conversion import DocumentConverter as Converter
from ..services.conversion import convert as _convert
from ..services.document_source import decode_main as decode_data
from ..services.document_source import load_from_url as get_main_from_url
from ..services.document_source import load_from_xml as get_main_from_xml
from ..services.page_downloader import PageDownloader as Downloader
from ..services.workspace import clean
from ..services.workspace import initialize as init

_default_config: Config | None = None

__all__ = [
    "Converter",
    "Downloader",
    "Mode",
    "clean",
    "convert",
    "decode_data",
    "get_main_from_url",
    "get_main_from_xml",
    "get_swf",
    "init",
    "main",
    "run",
]


def _config() -> Config:
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config


def __getattr__(name: str):
    """Лениво предоставляет прежнюю глобальную переменную ``cfg2``."""
    if name == "cfg2":
        return _config()
    raise AttributeError(name)


def get_swf(document) -> None:
    """Совместимый вызов загрузки и сборки SWF."""
    Downloader(document, _config()).run()


def convert(document) -> str:
    """Совместимый вызов преобразования документа."""
    return _convert(document, _config())


def main(config: dict, more: bool = False, initial: bool = True) -> bool:
    """Совместимый вызов сценария извлечения одного документа."""
    return ExtractionWorkflow(_config()).extract(
        config,
        scan_extra=more,
        initialize_workspace=initial,
    )


def run(*, debug: bool = False) -> int:
    """Запускает приложение с конфигурацией по умолчанию."""
    return _run(_config(), debug=debug)
