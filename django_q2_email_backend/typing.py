from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TypedDict

if TYPE_CHECKING:
    from email.mime.base import MIMEBase

    class RequiredEmailMessageData(TypedDict):
        cc: list[str] | None
        subject: str
        body: str
        from_email: str | None
        to: list[str] | None
        bcc: list[str] | None
        attachments: list[MIMEBase | tuple[str, str]] | None
        headers: dict[str, str] | None
        reply_to: list[str] | None

    class OptionalEmailMessageData(TypedDict, total=False):
        alternatives: list[tuple[str, str]] | None

    class EmailMessageData(RequiredEmailMessageData, OptionalEmailMessageData): ...
