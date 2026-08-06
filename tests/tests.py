from email.message import MIMEPart
from email.mime.text import MIMEText
from unittest import skipIf

import django
from django.core import mail
from django.test import TestCase
from django.test import override_settings

from django_q2_email_backend.backends import Q2EmailBackend


def make_mime_attachment() -> MIMEPart | MIMEText:
    # MIMEBase attachments are deprecated as of Django 6.0.
    if django.VERSION >= (6, 0):
        attachment = MIMEPart()
        attachment.set_content("Hello")
        return attachment
    return MIMEText("Hello")


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
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Subject")
        self.assertEqual(mail.outbox[0].body, "Message")
        self.assertEqual(mail.outbox[0].to, ["bar@example.com"])

    def test_send_html_email(self) -> None:
        message = mail.EmailMultiAlternatives(**self.message_data)
        message.attach_alternative("<p>HTML</p>", mimetype="text/html")

        num_sent = self.backend.send_messages([message])

        self.assertEqual(num_sent, 1)
        self.assertEqual(mail.outbox[0].alternatives, [("<p>HTML</p>", "text/html")])

    def test_send_email_with_attachment(self) -> None:
        message = mail.EmailMessage(**self.message_data)
        message.attach("hello.txt", "Hello", "text/plain")

        num_sent = self.backend.send_messages([message])

        self.assertEqual(num_sent, 1)
        self.assertEqual(
            mail.outbox[0].attachments, [("hello.txt", "Hello", "text/plain")]
        )

    def test_send_email_with_mime_attachment(self) -> None:
        message = mail.EmailMessage(**self.message_data)
        message.attach(make_mime_attachment())

        num_sent = self.backend.send_messages([message])

        self.assertEqual(num_sent, 1)
        sent = mail.outbox[0]
        self.assertEqual(len(sent.attachments), 1)
        self.assertIn("Hello", sent.message().as_string())

    def test_send_email_with_addresses_and_headers(self) -> None:
        message = mail.EmailMessage(
            **self.message_data,
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            reply_to=["reply@example.com"],
            headers={"X-Custom": "value"},
        )

        num_sent = self.backend.send_messages([message])

        self.assertEqual(num_sent, 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.cc, ["cc@example.com"])
        self.assertEqual(sent.bcc, ["bcc@example.com"])
        self.assertEqual(sent.reply_to, ["reply@example.com"])
        self.assertEqual(sent.extra_headers, {"X-Custom": "value"})
        self.assertEqual(
            sent.recipients(), ["bar@example.com", "cc@example.com", "bcc@example.com"]
        )


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

    def assert_invalid_using(self, using: str | None) -> None:
        options = {"using": using} if using is not None else {}
        mailers = {
            "default": {"BACKEND": MAILERS["default"]["BACKEND"], "OPTIONS": options}
        }
        with (
            override_settings(MAILERS=mailers),
            self.assertRaises(mail.InvalidMailer),
        ):
            _ = mail.mailers["default"]

    def test_using_is_required(self) -> None:
        self.assert_invalid_using(None)

    def test_using_must_not_be_self(self) -> None:
        self.assert_invalid_using("default")

    def test_using_must_be_configured(self) -> None:
        self.assert_invalid_using("nonexistent")
