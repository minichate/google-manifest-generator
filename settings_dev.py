from settings import *
import os

os.environ['ESDBLIB_LOG_DEBUG'] = 'w00t'

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