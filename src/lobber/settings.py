# Django settings for the lobber project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

BASE_DIR = '/home/leifj/work/sunet.se/lobber'
BASE_UI_URL = 'https://nordushare-dev.nordu.net'
BASE_URL = 'http://nordushare-dev.nordu.net'
APPLICATION_CTX = ''
NORDUSHARE_URL = BASE_UI_URL 
ANNOUNCE_URL = '%s:4711/announce' % BASE_URL

ADMINS = (
    ('Linus Nordberg', 'linus@nordu.net'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = '%s/db/nordushare.db' % BASE_DIR
DATABASE_USER = 'www-data'
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Stockholm'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = "%s/src/site-media" % BASE_DIR
ADMIN_MEDIA_ROOT = "/usr/lib/pymodules/python2.5/django/contrib/admin/media"
TORRENTS = "%s/torrents" % BASE_DIR

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/site-media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Used by the URLmiddleware
APPEND_SLASH = False

# Used by mail sender
SMTP_HOST = 'smtp.nordu.net'
SMTP_PORT = 25

# Make this unique, and don't share it with anybody.
SECRET_KEY = '79881b760f983c625fee66993d40d9ec997454fb9ce0e6cb4db99624265d1ffb'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'lobber.urlmiddleware.UrlMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'lobber.middleware.KeyMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware'
)

AUTHENTICATION_BACKENDS = (
    'lobber.backends.RemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'lobber.urls'

TEMPLATE_DIRS = (
    '%s/src/templ' % BASE_DIR,
)

LOGIN_URL = '/auth/login/'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',      # For the Permission model.
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'lobber.share',
    'lobber.auth'
)

LOBBER_LOG_FILE = "%s/logs/web.log" % BASE_DIR
import logging; LOBBER_LOG_LEVEL = logging.DEBUG
