from {{project_name}}.settings.base import *


DEBUG = True
TEMPLATE_DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'jenkins',
        'USER': 'jenkins',
        'PASSWORD': 'wvb3+zi%*v@+',
        'HOST': 'localhost',
    }
}

INSTALLED_APPS += (
    'django_jenkins',
)

PROJECT_APPS = []

JENKINS_TASKS = (
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes',
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.run_jshint',
)
