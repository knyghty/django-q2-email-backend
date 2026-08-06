from unittest import skipIf

import django
from django.core import mail
from django.test import TestCase
from django.test import override_settings

from django_q2_email_backend import utils
from django_q2_email_backend.backends import Q2EmailBackend

MAILERS = {
    "default": {
        "BACKEND": "django_q2_email_backend.backends.Q2EmailBackend",
        "OPTIONS": {"using": "locmem"},
    },
    "locmem": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"},
}


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


class TestSerialization(TestCase):
    def test_encoding(self) -> None:
        message = mail.EmailMessage(subject="Subject", body="Message")
        message.encoding = "iso-8859-1"

        round_tripped = utils.from_dict(utils.to_dict(message))

        self.assertEqual(round_tripped.encoding, "iso-8859-1")

    def test_encoding_absent(self) -> None:
        email_message_data = utils.to_dict(mail.EmailMessage(subject="Subject"))
        del email_message_data["encoding"]

        round_tripped = utils.from_dict(email_message_data)

        self.assertIsNone(round_tripped.encoding)


@skipIf(django.VERSION < (6, 1), "MAILERS was added in Django 6.1")
@override_settings(MAILERS=MAILERS)
class TestMailers(TestCase):
    def test_send_email(self) -> None:
        message = mail.EmailMessage(
            subject="Subject",
            body="Message",
            from_email="foo@example.com",
            to=["bar@example.com"],
        )

        num_sent = mail.mailers.default.send_messages([message])

        self.assertEqual(num_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Subject")

    def test_using_is_required(self) -> None:
        mailers = {"default": {"BACKEND": MAILERS["default"]["BACKEND"]}}
        with (
            override_settings(MAILERS=mailers),
            self.assertRaises(mail.InvalidMailer),
        ):
            _ = mail.mailers["default"]
