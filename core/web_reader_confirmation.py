from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from core.web_reader_adapter import extract_url_from_text


@dataclass
class WebReaderConfirmation:
    """Web Reader実行前の確認メッセージdry-run結果です。"""

    needs_confirmation: bool
    url: Optional[str]
    tool_name: Optional[str]
    action: Optional[str]
    message: str
    reason: str

    def to_dict(self):
        """checkやデバッグで扱いやすいdict形式にします。"""
        return {
            "needs_confirmation": self.needs_confirmation,
            "url": self.url,
            "tool_name": self.tool_name,
            "action": self.action,
            "message": self.message,
            "reason": self.reason,
        }


def build_web_reader_confirmation(user_input):
    """URL入力からWeb Reader実行前の確認メッセージだけを作ります。

    この関数はdry-run専用です。ToolRunnerもWebReaderAdapterのfetchも呼びません。
    """
    url = extract_url_from_text(user_input)

    if not url or not _is_http_url(url):
        return WebReaderConfirmation(
            needs_confirmation=False,
            url=None,
            tool_name=None,
            action=None,
            message="",
            reason="URLが見つかりませんでした。",
        )

    return WebReaderConfirmation(
        needs_confirmation=True,
        url=url,
        tool_name="web_reader",
        action="read_url",
        message=(
            "このURLをWeb Readerで読み取ってもよいですか？\n"
            f"{url}\n\n"
            "外部Webへアクセスするため、実行前に確認が必要です。"
        ),
        reason="外部Webアクセスにはユーザー確認が必要です。",
    )


def _is_http_url(url):
    parsed = urlparse(str(url))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
