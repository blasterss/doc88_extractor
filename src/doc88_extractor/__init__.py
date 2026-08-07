"""Инструменты для извлечения и преобразования предпросмотра DOC88."""

import importlib
import sys

__version__ = "2.2.1"

# Старые плоские пути остаются доступными без дублирования файлов в корне.
_COMPATIBLE_MODULES = {
    "application": "compat.application",
    "binary_tools": "toolchain.binary_tools",
    "cli": "presentation.cli",
    "coder": "core.coder",
    "compressor": "ebt.compressor",
    "config": "core.config",
    "console": "presentation.console",
    "conversion": "services.conversion",
    "document_catalog": "services.document_catalog",
    "document_config": "core.document_config",
    "document_source": "services.document_source",
    "ebt_import": "compat.ebt_import",
    "ebt_parser": "ebt.ebt_parser",
    "ffdec_manager": "toolchain.ffdec_manager",
    "file_system": "infrastructure.file_system",
    "gen_cfg": "core.gen_cfg",
    "get_more": "ebt.get_more",
    "http_client": "infrastructure.http_client",
    "interaction": "presentation.interaction",
    "java_runtime": "toolchain.java_runtime",
    "logging_utils": "infrastructure.logging_utils",
    "page_downloader": "services.page_downloader",
    "release_client": "infrastructure.release_client",
    "updater": "toolchain.updater",
    "utils": "compat.utils",
    "workflow": "app.workflow",
    "workspace": "services.workspace",
}

for _old_name, _new_name in _COMPATIBLE_MODULES.items():
    sys.modules[f"{__name__}.{_old_name}"] = importlib.import_module(f".{_new_name}", __name__)

del _old_name, _new_name
