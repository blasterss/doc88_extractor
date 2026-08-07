"""Фасад совместимости для прежнего набора вспомогательных функций."""

from ..infrastructure.file_system import extract_archive as extract
from ..infrastructure.file_system import ospath
from ..infrastructure.file_system import read_bytes as load_file
from ..infrastructure.file_system import read_text as read_file
from ..infrastructure.file_system import safe_filename as special_path
from ..infrastructure.file_system import write_bytes as write_file
from ..infrastructure.file_system import write_text as writes_file
from ..infrastructure.http_client import download
from ..infrastructure.http_client import get as _get
from ..infrastructure.logging_utils import write_log as logw
from ..infrastructure.release_client import GitHubRelease
from ..presentation.console import confirm as choose
from ..presentation.console import wait_for_enter as input_break

__all__ = [
    "GitHubRelease",
    "choose",
    "download",
    "extract",
    "get_request",
    "input_break",
    "load_file",
    "logw",
    "ospath",
    "read_file",
    "special_path",
    "write_file",
    "writes_file",
]


def get_request(
    url: str,
    referer: bool = True,
    cffi: bool = False,
    content_type: str = "text/html; charset=utf-8",
    stream: bool = False,
    timeout: int = 30,
):
    """Совместимый адаптер HTTP-клиента."""
    return _get(
        url,
        referer=referer,
        browser_impersonation=cffi,
        content_type=content_type,
        stream=stream,
        timeout=timeout,
    )
