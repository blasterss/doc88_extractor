"""Построение конфигурации документа из нормализованных PH/PK."""

from typing import Any

from .coder import encode


def build(
    headers: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    document_name: str = "",
    host: str = "https://cdn2.doc88.com",
) -> dict:
    """Создаёт словарь, принимаемый моделью ``GenConfig``."""
    if not headers:
        raise ValueError("Отсутствуют файлы PH.")
    if not pages:
        raise ValueError("Отсутствуют файлы PK.")

    pages.sort(key=lambda item: int(item["page"]))
    headers.sort(key=lambda item: int(item["level"]))

    page_ids = []
    for page in pages:
        width = page.get("width")
        height = page.get("height")
        dimensions = f"{width}-{height}" if width and height else "612-858"
        page_ids.append(
            f"{page['level']}-{dimensions}-{page['headsize']}-{page['chunk_size']}"
        )

    document_id = str(pages[0]["p_code"])
    return {
        "headerInfo": ",".join(f'"{item["chunk_size"]}"' for item in headers),
        "p_swf": headers[0]["p_swf"],
        "ebt_host": host,
        "p_code": document_id,
        "pageInfo": encode(",".join(page_ids)),
        "p_name": document_name or f"Неизвестный документ {document_id}",
        "p_upload_date": str(pages[0]["p_swf"]).split("-")[1],
        "pageCount": len(pages),
        "p_download": "0",
        "p_doc_format": "pdf",
        "p_pagecount": str(len(pages)),
    }
