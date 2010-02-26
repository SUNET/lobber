# -*- coding: utf-8 -*-

import sys
import datetime
import re

from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect,  Http404
from django.views.decorators.cache import never_cache
from django import forms
from django.contrib import auth
from django.db.models import Q
from django.contrib.auth.models import User
from django.db import IntegrityError

from lobber.settings import LOBBER_LOG_FILE

import lobber.log
logger = lobber.log.Logger("web", LOBBER_LOG_FILE)


# Helpers
def req_meta(request, field):
    return request.META.get(field, "N/A")


@never_cache
def logout(request):
    
    username = request.user.username
    logger.info("Logout for user %s" % username)
    auth.logout(request)

    return HttpResponseRedirect('/Shibboleth.sso/Logout')

@never_cache
def login(request):
    if request.user.is_authenticated():
        update = False

        for attrib_name, meta_name in (("first_name", "HTTP_GIVENNAME"),
                                       ("last_name", "HTTP_SN"),
                                       ("email", "HTTP_MAIL")):

            attrib_value = getattr(request.user, attrib_name)
            meta_value = request.META.get(meta_name)
            if meta_value and not attrib_value:
                setattr(request.user, attrib_name, meta_value)
                update = True

        if request.user.password == "":
            request.user.password = "(not used for federated logins)"
            update = True

        if update:
            request.user.save()

        logger.info("Accepted federated login for user %s from %s" % (request.user.username,
                                                                      req_meta(request, "REMOTE_ADDR")))

        # On a sucessful login, just do the redirect if one is requested
        next = request.session.get("after_login_redirect", None)
        if next is not None:
            return HttpResponseRedirect(next)

    else:
        logger.warning("Failed federated login for user %s from %s" % (request.user.username,
                                                                       req_meta(request, "REMOTE_ADDR")))

    # Used for both failure and some success cases (when not redirecting)
    return render_to_response('share/login.html',
                              {'user': request.user,
                               'meta': request.META,
                               })

