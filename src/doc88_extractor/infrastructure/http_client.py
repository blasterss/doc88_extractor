"""HTTP-доступ к DOC88 и загрузка бинарных ресурсов."""

import requests
from curl_cffi import requests as requests_cffi
from retrying import retry

from .file_system import write_bytes


def get(
    url: str,
    *,
    referer: bool = True,
    browser_impersonation: bool = False,
    content_type: str = "text/html; charset=utf-8",
    stream: bool = False,
    timeout: int = 30,
):
    """Выполняет GET обычным клиентом или с браузерным отпечатком."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0"
        ),
        "Content-Type": content_type,
        "Referer": "https://www.doc88.com/",
    }
    if not referer:
        headers.pop("Referer")
    if not content_type:
        headers.pop("Content-Type")
    client = requests_cffi if browser_impersonation else requests
    kwargs = {"headers": headers, "stream": stream, "timeout": timeout}
    if browser_impersonation:
        kwargs["impersonate"] = "chrome"
    return client.get(url, **kwargs)


@retry(stop_max_attempt_number=3, wait_fixed=500)
def download(url: str, destination: str) -> None:
    """Загружает файл с тремя попытками."""
    write_bytes(get(url, referer=False).content, destination)
