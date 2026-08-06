from typing import TYPE_CHECKING
from typing import Any

import django
from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django_q.tasks import async_task

from . import utils

if django.VERSION >= (6, 1):
    from django.core.mail import InvalidMailer

if TYPE_CHECKING:
    from django.core.mail import EmailMessage

    from .typing import EmailMessageData

Q2_EMAIL_BACKEND = getattr(
    settings, "Q2_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)


def send_message(
    serialized_email_message: "EmailMessageData",
    init_kwargs: dict[str, Any],
    using: str | None = None,
) -> None:
    email_message = utils.from_dict(serialized_email_message)
    if using is not None:
        email_message.send(using=using)
        return
    connection = get_connection(backend=Q2_EMAIL_BACKEND, **init_kwargs)
    connection.send_messages([email_message])


class Q2EmailBackend(BaseEmailBackend):
    def __init__(
        self,
        fail_silently: bool = False,
        *,
        using: str | None = None,
        **kwargs: Any,  # NOQA: ANN401
    ) -> None:
        self.using = using
        self.init_kwargs: dict[str, Any] = {}
        if django.VERSION >= (6, 1) and hasattr(settings, "MAILERS"):
            alias = kwargs.get("alias")
            if using is None:
                msg = (
                    "Q2EmailBackend requires a 'using' option naming the MAILERS "
                    "alias to send messages with."
                )
                raise InvalidMailer(msg, alias=alias)
            if using == alias:
                msg = f"The 'using' option must not name this mailer, {using!r}."
                raise InvalidMailer(msg, alias=alias)
            if using not in settings.MAILERS:
                msg = f"The 'using' option names an unconfigured mailer, {using!r}."
                raise InvalidMailer(msg, alias=alias)
            super().__init__(**kwargs)
        else:
            self.init_kwargs = kwargs
            super().__init__(fail_silently)

    def send_messages(self, email_messages: list["EmailMessage"]) -> int:
        num_sent = 0
        for email_message in email_messages:
            serialized_email_message = utils.to_dict(email_message)
            async_task(
                "django_q2_email_backend.backends.send_message",
                serialized_email_message,
                self.init_kwargs,
                self.using,
            )
            num_sent += 1
        return num_sent
