import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'lobber.settings'

sys.path.append('/var/www/lobber/src')
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
