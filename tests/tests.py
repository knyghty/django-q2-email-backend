from django.core import mail
from django.test import TestCase

from django_q2_email_backend.backends import Q2EmailBackend


class TestEmailBackend(TestCase):
    def setUp(self) -> None:
        self.backend = Q2EmailBackend()
        self.message_data = {
            "subject": "Subject",
            "body": "Message",
            "from_email": "foo@example.com",
            "to": ["bar@example.com"],
        }

    def test_send_email(self) -> None:
        message = mail.EmailMessage(**self.message_data)

        num_sent = self.backend.send_messages([message])

        self.assertEqual(num_sent, 1)

    def test_send_html_email(self) -> None:
        message = mail.EmailMultiAlternatives(**self.message_data)
        message.attach_alternative("<p>HTML</p>", mimetype="text/html")

        num_sent = self.backend.send_messages([message])

        self.assertEqual(num_sent, 1)
