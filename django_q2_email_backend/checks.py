from typing import Any

from django.conf import settings
from django.core.checks import CheckMessage
from django.core.checks import Error
from django.core.checks import register
from django.utils.module_loading import import_string

from .backends import Q2EmailBackend


def is_queued(backend_path: str | None) -> bool:
    if not backend_path:
        return False
    try:
        backend_class = import_string(backend_path)
    except ImportError:
        return False
    return isinstance(backend_class, type) and issubclass(backend_class, Q2EmailBackend)


@register
def check_using_options(
    app_configs: Any,  # NOQA: ANN401
    **kwargs: Any,  # NOQA: ANN401
) -> list[CheckMessage]:
    if not settings.is_overridden("MAILERS"):
        return []

    errors: list[CheckMessage] = []
    for alias, config in settings.MAILERS.items():
        if not is_queued(config.get("BACKEND")):
            continue
        using = config.get("OPTIONS", {}).get("using")
        if using is None:
            errors.append(
                Error(
                    f"MAILERS[{alias!r}] has no 'using' option.",
                    hint="Name the mailer that should send the queued messages.",
                    id="q2_email_backend.E001",
                )
            )
        elif using not in settings.MAILERS:
            errors.append(
                Error(
                    f"MAILERS[{alias!r}] names an unconfigured mailer, {using!r}.",
                    hint=f"Add a {using!r} entry to MAILERS.",
                    id="q2_email_backend.E002",
                )
            )
        elif is_queued(settings.MAILERS[using].get("BACKEND")):
            errors.append(
                Error(
                    f"MAILERS[{alias!r}] names a queued mailer, {using!r}.",
                    hint="Messages sent through it would be queued again, not sent.",
                    id="q2_email_backend.E003",
                )
            )
    return errors
