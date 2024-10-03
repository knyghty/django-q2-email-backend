DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django_q",
    "django_q2_email_backend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

SECRET_KEY = "django-insecure-dummy"  # NOQA: S105

Q_CLUSTER = {
    "orm": "default",
    "sync": True,
}

EMAIL_BACKEND = "django_q2_email_backend.backends.Q2EmailBackend"
Q2_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
