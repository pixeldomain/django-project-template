import os
from {{project_name}}.settings.base import *


SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '{{project_name}}',
        'USER': '{{project_name}}',
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': 'localhost',
    }
}
