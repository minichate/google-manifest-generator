from settings import *

DB_DIRECTORY = PROJECT_ROOT

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase'
    }
}

TEMPLATE_CONTEXT_PROCESSORS = (
)

TEMPLATE_DIRS += [
    PROJECT_ROOT + '/dev_templates'
]