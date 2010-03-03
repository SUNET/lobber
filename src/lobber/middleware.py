# http://docs.djangoproject.com/en/1.1/topics/http/middleware/

from datetime import datetime as dt
import re

from django.contrib import auth
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist

from lobber.share.models import UserProfile
from lobber.settings import LOBBER_LOG_FILE, APPLICATION_URL
import lobber.log
logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

class KeyMiddleware(object):
    """
    """
    def process_request(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the KeyMiddleware class.")
        # Look for 'lkey' in query part of URL.
        secret = request.REQUEST.get('lkey', None)
        if secret is None:
            return

        # TODO: Sanitize secret (a.k.a. un-bobby-tablify it).
        username = 'key:' + secret
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            logger.info("%s: user not found" % username)
            return

        try:
            profile = user.profile.get()
        except ObjectDoesNotExist:
            logger.error("%s: user profile not found" % username)
            return

        if profile.expiration_date is not None and \
               profile.expiration_date <= dt.now():
            logger.info("%s: key expired" % secret)
            return

        filtermatch_flag = False
        cmd = request.path[len('/%s/'%APPLICATION_URL):]
        for e in profile.urlfilter:
            if re.match(e, cmd):
                filtermatch_flag = True
                break
        if not filtermatch_flag:
            logger.info("%s: no match for url in filter (url=%s, filter=%s)"
                        % (username, cmd, profile.urlfilter))
            return

        if request.user.is_authenticated():
            if request.user.username == self.clean_username(username, request):
                logger.info("user %s already authenticated" % username)
                return                  # All ok.
        xxx = auth.authenticate(remote_user=username)
        logger.info("authenticated %s, got %s" % (username, xxx))
        if xxx:
            profile.displayname = username
            request.user = xxx
            auth.login(request, xxx)
        
    # TODO: Add a configure_user(user) method?
    
    def clean_username(self, username, request):
        """
        Allows the backend to clean the username, if the backend defines a
        clean_username method.
        """
        backend_str = request.session[auth.BACKEND_SESSION_KEY]
        backend = auth.load_backend(backend_str)
        try:
            username = backend.clean_username(username)
        except AttributeError: # Backend has no clean_username method.
            pass
        return username
