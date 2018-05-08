from __future__ import absolute_import

from .settings import *

DEBUG = True

INSTALLED_APPS += [
    'django_extensions',
]


# Databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "sordas_main",
        "USER": "sordas",
        "PASSWORD": "sordas",
        "HOST": "",
        "PORT": "",
    }
}
