# Django settings for the lobber project.
from os import path

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SETTINGS_DIR = path.dirname(path.abspath(__file__))
BASE_DIR = path.dirname(path.dirname(SETTINGS_DIR))
TORRENTS = "%s/torrents" % BASE_DIR
APP_ADDR = 'localhost:8000'
BASE_UI_URL = 'http://' + APP_ADDR
BASE_URL = BASE_UI_URL
APPLICATION_CTX = ''
NORDUSHARE_URL = BASE_UI_URL
TRACKER_EXIST_URL = '%s/torrent/exists' % BASE_URL

#TRACKER_ADDR = 'tracker-dev.lobber.se:443'
TRACKER_ADDR = 'localhost:8000'
ANNOUNCE_BASE_URL = 'http://' + TRACKER_ADDR
ANNOUNCE_URL = ANNOUNCE_BASE_URL + '/tracker/announce'
SCRAPE_URL = '/tracker/scrape'

DROPBOX_DIR = '%s/dropbox' % BASE_DIR
#TRANSMISSION_RPC = 'http://transmission:transmission@localhost:9091'

STOMP_HOST = 'localhost'
STOMP_PORT = 61613
ORBITED_PREFIX = 'http://localhost:9001'

ADMINS = (
    ('Johan Lundberg', 'lundberg@nordu.net'),
    ('Johan Berggren', 'jbn@nordu.net')
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'lobber',                      # Or path to database file if using sqlite3.
        'USER': 'lobber',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

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

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/media/"

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = "%s/src/staticfiles" % BASE_DIR

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/site-media/"

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "%s/src/site-media" % BASE_DIR,
    )

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    )

# Used by the URLmiddleware
APPEND_SLASH = False

# Used by mail sender
SMTP_HOST = 'localhost'
SMTP_PORT = 25

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'MAKE_UNIQUE_PER_INSTALLATION'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'lobber.urlmiddleware.UrlMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'lobber.middleware.KeyMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
    'django.contrib.staticfiles',
    'django_extensions',
    'django_co_connector',
    'django_co_acls',
    'lobber.extensions',
    'tagging',
    'lobber.userprofile',
    'lobber.share',
    'lobber.links',
    'lobber.tracker',
    'lobber.auth'
)

LOBBER_LOG_FILE = "%s/logs/web.log" % BASE_DIR
import logging; LOBBER_LOG_LEVEL = logging.DEBUG
