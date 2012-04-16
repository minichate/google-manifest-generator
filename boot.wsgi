#!/usr/bin/python
# vim: ft=python ts=4 sw=4 et ai:

import sys, os

sys.path.append('/etc/e-smith/web/django')
sys.path.append('/etc/e-smith/web/django/manifest')
os.environ['DJANGO_SETTINGS_MODULE'] = 'manifest.settings'

import django.core.handlers.wsgi

_application = django.core.handlers.wsgi.WSGIHandler()

def application(environ, start_response):
    environ['HTTPS'] = 'on'
    return _application(environ, start_response)

    