from __future__ import annotations

from http import HTTPStatus
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .constants import DEFAULT_HTTP_TIMEOUT, REQUEST_HEADERS
from .models import ShortcutMetadata


class IconDownloadError(RuntimeError):
    """Raised when a Steam icon cannot be downloaded."""


class SteamIconClient:
    """Small HTTP client responsible for downloading Steam icon files."""

    def __init__(self, timeout: int = DEFAULT_HTTP_TIMEOUT) -> None:
        self.timeout = timeout

    def build_icon_url(self, metadata: ShortcutMetadata) -> str:
        return (
            "https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/"
            f"apps/{metadata.steam_id}/{metadata.icon_name}"
        )

    def download_icon_bytes(self, metadata: ShortcutMetadata) -> bytes:
        icon_url = self.build_icon_url(metadata)
        request = Request(icon_url, headers=REQUEST_HEADERS)

        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != HTTPStatus.OK:
                    raise IconDownloadError(
                        f"下载图标失败: {icon_url} (HTTP {response.status})"
                    )
                return response.read()
        except HTTPError as exc:
            raise IconDownloadError(
                f"下载图标失败: {icon_url} (HTTP {exc.code})"
            ) from exc
        except URLError as exc:
            raise IconDownloadError(f"下载图标失败: {icon_url} ({exc})") from exc

    def close(self) -> None:
        return None
