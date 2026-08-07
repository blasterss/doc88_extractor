"""Совместимый фасад импорта EBT."""

from ..core.document_config import build
from ..ebt.ebt_parser import parse_xml as import_xml
from ..ebt.ebt_parser import scan_directory as import_ebt

__all__ = ["build_cfg", "import_ebt", "import_xml"]


def build_cfg(
    ph_list: list[dict],
    pk_list: list[dict],
    doc_name: str = "",
    ebt_host: str = "https://cdn2.doc88.com",
) -> dict:
    """Адаптирует прежние имена аргументов к новому построителю."""
    return build(ph_list, pk_list, doc_name, ebt_host)
