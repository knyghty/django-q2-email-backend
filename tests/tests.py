import warnings
from email.message import MIMEPart
from email.mime.text import MIMEText
from unittest import skipIf

import django
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from django.test import TestCase
from django.test import override_settings

from django_q2_email_backend import utils
from django_q2_email_backend.backends import Q2EmailBackend
from django_q2_email_backend.checks import check_using_options


def make_mime_attachment() -> MIMEPart | MIMEText:
    if django.VERSION >= (6, 0):
        attachment = MIMEPart()
        attachment.set_content("Hello")
        return attachment
    return MIMEText("Hello")


QUEUED = "django_q2_email_backend.backends.Q2EmailBackend"

MAILERS = {
    "default": {
        "BACKEND": QUEUED,
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

    def test_no_deprecation_warnings(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Q2EmailBackend()

        self.assertEqual([str(warning.message) for warning in caught], [])

    def test_using_requires_mailers(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            Q2EmailBackend(using="locmem")

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


@skipIf(django.VERSION < (6, 1), "MAILERS was added in Django 6.1")
class TestChecks(SimpleTestCase):
    def assert_error(self, mailers: dict[str, object], error_id: str) -> None:
        with override_settings(MAILERS=mailers):
            errors = check_using_options(None)

        self.assertEqual([error.id for error in errors], [error_id])

    def test_valid(self) -> None:
        with override_settings(MAILERS=MAILERS):
            self.assertEqual(check_using_options(None), [])

    def test_no_mailers(self) -> None:
        self.assertEqual(check_using_options(None), [])

    def test_backend_that_is_not_a_class(self) -> None:
        with override_settings(MAILERS={"default": {"BACKEND": "os.path.join"}}):
            self.assertEqual(check_using_options(None), [])

    def test_using_is_required(self) -> None:
        self.assert_error(
            {"default": {"BACKEND": QUEUED}},
            "q2_email_backend.E001",
        )

    def test_using_must_be_configured(self) -> None:
        self.assert_error(
            {"default": {"BACKEND": QUEUED, "OPTIONS": {"using": "nonexistent"}}},
            "q2_email_backend.E002",
        )

    def test_using_must_not_be_self(self) -> None:
        self.assert_error(
            {"default": {"BACKEND": QUEUED, "OPTIONS": {"using": "default"}}},
            "q2_email_backend.E003",
        )

    def test_using_must_not_be_another_queued_mailer(self) -> None:
        with override_settings(
            MAILERS={
                "default": {"BACKEND": QUEUED, "OPTIONS": {"using": "other"}},
                "other": {"BACKEND": QUEUED, "OPTIONS": {"using": "default"}},
            }
        ):
            errors = check_using_options(None)

        self.assertEqual(
            [error.id for error in errors],
            ["q2_email_backend.E003", "q2_email_backend.E003"],
        )
