"""Получение и декодирование метаданных документа DOC88."""

import json
import re
from xml.parsers.expat import ExpatError

from ..core.coder import decode, key2
from ..core.document_config import build
from ..ebt.ebt_parser import parse_xml
from ..infrastructure.http_client import get
from ..presentation.console import confirm

DOC88_DOMAIN = "doc88.com"
CDN_DOMAIN = "doc88.piglin.eu.org"
DOCINFO_PATH = "doc.php?act=info&p_code="


def decode_main(data: str) -> dict:
    """Декодирует аргумент ``m_main.init`` в словарь конфигурации."""
    try:
        return json.loads(decode(data))
    except json.JSONDecodeError as error:
        raise ValueError("Не удалось прочитать данные m_main.") from error
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError(
            "Не удалось декодировать m_main: возможно, изменились ключи."
        ) from error


def load_from_xml(document_id: str) -> dict:
    """Получает XML-описание документа и преобразует его в конфигурацию."""
    url = f"https://www.{DOC88_DOMAIN}/{DOCINFO_PATH}{document_id}"
    response = get(url, referer=True, browser_impersonation=True)
    if not response.text:
        raise KeyError("Сервер вернул пустое описание документа.")
    return build(*parse_xml(decode(response.text, key2)))


def load_from_url(url: str, method: int = 1) -> dict | bool:
    """Получает конфигурацию по URL через XML API или HTML страницы."""
    if f"{DOC88_DOMAIN}/p-" not in url and f"{CDN_DOMAIN}/p-" not in url:
        raise ValueError("Некорректный URL DOC88.")

    if method == 1:
        try:
            document_id = url.split("/p-", 1)[1].split(".html", 1)[0]
            if document_id.isdigit():
                return load_from_xml(document_id)
        except (KeyError, TypeError, ExpatError) as error:
            print(f"Способ 1 не сработал, переключение на способ 2: {error}")
        return load_from_url(url, method=2)

    response = get(url, referer=True, browser_impersonation=True)
    if response.status_code == 404:
        raise FileNotFoundError("Документ не найден (HTTP 404).")

    match = re.search(r'm_main\.init\("(.*)"\);', response.text)
    if match:
        return decode_main(match.group(1))

    if "网络环境安全验证" in response.text:
        print("Обнаружена проверка WAF.")
        if confirm("Использовать CDN? (Y/n): "):
            cdn_url = f"https://{CDN_DOMAIN}{url.split(DOC88_DOMAIN)[1]}"
            return load_from_url(cdn_url)
        return False
    raise ValueError("На странице не найдены данные m_main.")
