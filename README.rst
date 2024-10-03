=======================
Django Q2 Email Backend
=======================

An asynchronous Django email backend for Dgjango Q2

------------
Requirements
------------

* `Django <https://www.djangoproject.com/>`_
* `Django Q2 <https://github.com/django-q2/django-q2>`_

------------
Installation
------------

* Install ``django-q2-email-backend``:

.. code-block:: bash

    pip install django-q2-email-backend

* Add ``django_q2_email_backend`` to ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = (
        # other apps
        "django_q2_email_backend",
    )

You must then set django-q2-email-backend as your ``EMAIL_BACKEND``:

.. code-block:: python

    EMAIL_BACKEND = "django_q2_email_backend.backends.Q2EmailBackend"

By default django-q2-email-backend will use Django's builtin ``SMTP`` email backend
for the actual sending of the mail. If you'd like to use another backend, you
may set it in ``Q2_EMAIL_BACKEND`` just like you would normally have set
``EMAIL_BACKEND`` before you were using Q2. In fact, the normal installation
procedure will most likely be to get your email working using only Django, then
change ``EMAIL_BACKEND`` to ``Q2_EMAIL_BACKEND``, and then add the new
``EMAIL_BACKEND`` setting from above.


Credits
-------

Some code around serializing emails was taken from `joeyespo/django-q-email`_

This package was created with Cookiecutter_ and the `knyghty/cookiecutter-django-package`_ project template.

.. _`joeyespo/django-q-email`: https://github.com/joeyespo/django-q-email
.. _Cookiecutter: https://github.com/cookiecutter/cookiecutter
.. _`knyghty/cookiecutter-django-package`: https://github.com/knyghty/cookiecutter-django-package
