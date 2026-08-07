"""Чтение метаданных последнего выпуска GitHub."""

from .http_client import get


class GitHubRelease:
    """Версия и набор доступных файлов одного выпуска."""

    def __init__(self, repository: str, asset_index: int = -1) -> None:
        data = get(
            f"https://api.github.com/repos/{repository}/releases/latest",
            referer=False,
        ).json()
        assets = data["assets"]
        self.latest_version: str = data["tag_name"]
        self.releases: dict[str, str] = {
            asset["name"]: asset["browser_download_url"] for asset in assets
        }
        self.download_url: str | None = None
        self.name: str | None = None
        if asset_index == -1:
            return
        asset = assets[asset_index]
        self.download_url = asset["browser_download_url"]
        self.name = asset["name"]
