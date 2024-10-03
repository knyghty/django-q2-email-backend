from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django_q.tasks import async_task

from . import utils

Q2_EMAIL_BACKEND = getattr(
    settings, "Q2_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)


class Q2EmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently)
        self.init_kwargs = kwargs

    def send_messages(self, email_messages):
        num_sent = 0
        for email_message in email_messages:
            serialized_email_message = utils.to_dict(email_message)
            async_task(self.send_message, serialized_email_message)
            num_sent += 1
        return num_sent

    def send_message(self, serialized_email_message):
        email_message = utils.from_dict(serialized_email_message)
        email_message.connection = get_connection(
            backend=Q2_EMAIL_BACKEND, **self.init_kwargs
        )
        email_message.send()
