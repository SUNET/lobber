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

from lobber.settings import BASE_DIR, MEDIA_ROOT, LOGIN_URL, ANNOUNCE_URL, NORDUSHARE_URL, LOBBER_LOG_FILE

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
    return render_to_response('share/login.html',{'user': request.user,'next': request.REQUEST.get("next")});

def login_federated(request):
    if request.user.is_authenticated():
        update = False

        for attrib_name, meta_name in (("first_name", "HTTP_GIVENNAME"),
                                       ("last_name", "HTTP_SN"),
                                       ("email", "HTTP_MAIL")):

            attrib_value = getattr(request.user, attrib_name)
            meta_value = request.META.get(meta_name)
            if meta_value != "(null)":
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
        logger.info(request)
        next = request.REQUEST.get("next", None)
	logger.info(next)
        if next is None:
	    return render_to_response("share/login.html",{"user": request.user});
        else:
            return HttpResponseRedirect(next)

    else:
        logger.warning("Failed federated login for user %s from %s" % (request.user.username,
                                                                       req_meta(request, "REMOTE_ADDR")))

