# coding=utf-8
"""
WSGI config for oecloud_dashboard project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys

try:
    sys.path.insert(0, os.sep.join(os.path.abspath(__file__).split(os.sep)[:-2]))
except:
    pass

from django.core.wsgi import get_wsgi_application

reload(sys)
sys.setdefaultencoding('utf-8')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_wsgi_application()
