from django.core import mail
from django.test import TestCase

from django_q2_email_backend.backends import Q2EmailBackend


class TestEmailBackend(TestCase):
    def setUp(self):
        self.backend = Q2EmailBackend()
        self.message = mail.EmailMultiAlternatives(
            subject="Subject",
            body="Message",
            from_email="foo@example.com",
            to=["bar@example.com"],
        )
        self.message.attach_alternative("<p>HTML</p>", mimetype="text/html")

    def test_send_email(self):
        num_sent = self.backend.send_messages([self.message])

        self.assertEqual(num_sent, 1)
