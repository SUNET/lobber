# -*- coding: utf-8 -*-


from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist

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
    return render_to_response('share/login.html',{'user': request.user,'next': request.REQUEST.get("next")});

def login_federated(request):
    def logfailure():
        username = request.user.username
        logger.warning("Failed federated login for user %s from %s" %
                       (username, req_meta(request, "REMOTE_ADDR")))
    
    # Authenticated?
    if not request.user.is_authenticated():
        logfailure()
        return render_to_response('share/login.html',{'error': "Authentication failed",'next': request.REQUEST.get("next")});
    username = request.user.username
    
    # Key users ('key:<secret>') must already have a profile -- for
    # url filtering.
    profile = None
    try:
        profile = request.user.profile.get()
    except ObjectDoesNotExist:
        if username.startswith('key:'):
            logger.error("Key user %s doesn't have a profile" % username)
            logfailure()
            return

    update_user = False
    for attrib_name, meta_name in (("first_name", "HTTP_GIVENNAME"),
                                   ("last_name", "HTTP_SN"),
                                   ("email", "HTTP_MAIL")):

        attrib_value = getattr(request.user, attrib_name)
        meta_value = request.META.get(meta_name)
        if meta_value != "(null)":
            setattr(request.user, attrib_name, meta_value)
            update_user = True

    if request.user.password == "":
        request.user.password = "(not used for federated logins)"
        update_user = True

    if update_user:
        request.user.save()

    # Get or create user profile.
    if profile is None:
        default_profile = {'user': request.user,
                           'creator': request.user,
                           'display_name': '',
                           'entitlements': '',
                           'urlfilter': '.*', # Logged in users can do everything.
                           'expiration_date': None}
        profile, created = request.user.profile.get_or_create(defaults=default_profile)
        if created:
            logger.info("Created user profile for user %s" % username)

    update_profile = False
    entitlement_in = request.META.get('HTTP_ENTITLEMENT')
    if entitlement_in != "(null)":
        profile.entitlements = entitlement_in.replace(';', ' ')
        update_profile = True

    display_name_in = request.META.get('HTTP_DISPLAYNAME')
    if display_name_in == None or display_name_in == "(null)":
        display_name_in = request.META.get('HTTP_CN')
    if display_name_in != None and display_name_in != "(null)":
        profile.display_name = display_name_in
        update_profile = True

    if update_profile:
        profile.save()

    # Successful login.
    logger.debug("User %s profile: %s" % (username, repr(profile)))
    logger.info("Accepted federated login for user %s from %s" % (username,
                                                                  req_meta(request, "REMOTE_ADDR")))

    # On a sucessful login, just do the redirect if one is requested
    next = request.REQUEST.get("next", None)
    if next is None:
        return render_to_response("share/login.html",{"user": request.user});
    else:
        return HttpResponseRedirect(next)
