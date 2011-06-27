# http://docs.djangoproject.com/en/1.1/topics/http/middleware/

from datetime import datetime as dt
import re

from django.contrib import auth
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from lobber.common import HttpResponseNotAuthorized
from lobber.torrenttools import bencode
from lobber.settings import DEBUG, LOBBER_LOG_FILE
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
        # Look for 'lkey' in query part of URL and in the X_LOBBER_KEY header.
        secret = request.REQUEST.get('lkey', None)
        if secret is None:
            secret = request.META.get('HTTP_X_LOBBER_KEY', None)
        if secret is None:
            return                      # Fail

        # TODO: Sanitize secret (a.k.a. un-bobby-tablify it).
        username = 'key:' + secret
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            logger.info("%s: user not found" % username)
            return HttpResponseNotAuthorized('Not a valid key.')

        try:
            profile = user.profile.get()
        except ObjectDoesNotExist:
            logger.error("%s: user profile not found" % username)
            return HttpResponseNotAuthorized('Not a valid key.')

        if profile.expiration_date is not None and \
                                           profile.expiration_date <= dt.now():
            logger.info("%s: key expired" % secret)
            return HttpResponseNotAuthorized('The key has expired.')

        filtermatch_flag = False
        cmd = request.path
        urlfilter = profile.urlfilter.split()
        for e in urlfilter:
            if re.match(e, cmd): # Note: Implicit `^' starting the RE.
                filtermatch_flag = True
                break
        if not filtermatch_flag:
            logger.info("%s: no match for url in filter (url=%s, filter=%s)"
                        % (username, cmd, urlfilter))
            return HttpResponseNotAuthorized('Not a valid key for that URL.')

        # Authenticate and login user.
        auth_user = auth.authenticate(username=username, password=username)
        if auth_user:
            profile.displayname = username
            request.user = auth_user
            auth.login(request, auth_user)
            request.session.flush()
        else:
            logger.debug("%s: failed authentication" % username)
            return HttpResponseNotAuthorized('Failed to authenticate.')

        # EPIC SUCCESS!!!  This is where we do anything needed for an
        # authenticated and logged in user.
        
    def process_exception(self, request, exception):
        '''
        Handles uncaught exceptions in KeyMiddleware.
        '''
        logger.error("KeyMiddleware uncaught error: %s" % exception)
        # Send a bencoded response to a torrent client if the request came
        # in to the tracker.
        if request.META['PATH_INFO'].split('/')[1] == 'tracker':
                return HttpResponse(bencode({'failure reason':
                                            '%s' % exception}),
                                            mimetype='text/plain')
        # If it's a 404, just let Django handle it as always.
        if isinstance(exception, Http404):
            return None
        # Don't show a user friendly error page if DEBUG is True in settings.py.
        elif not DEBUG:
            host = request.META['HTTP_HOST']
            path = request.META['PATH_INFO']
            # Return a user friendly error page.
            return render_to_response('unknown_error.html', 
                                      {'exception': '%s' % exception,
                                      'url': '%s%s' % (host, path)})
        
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

    # TODO: Add a configure_user(user) method?
