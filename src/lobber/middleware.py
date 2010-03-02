# http://docs.djangoproject.com/en/1.1/topics/http/middleware/

from datetime import datetime as dt
import re

from django.contrib import auth
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

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
        """
        qd = None
        if request.method == 'GET':
            qd = request.GET
        elif request.method == 'POST':
            qd = request.POST
        """
        secret = request.REQUEST.get('lkey', None)
        if not secret:
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

        if profile.expiration_date <= dt.now():
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

        profile.displayname = username
        request.user = user
        auth.login(request, user)
        
    # TODO: Add a configure_user(user) method?
    