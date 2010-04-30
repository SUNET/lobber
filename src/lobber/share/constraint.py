from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils.html import escape
from django.contrib.auth.models import User
from lobber.share.models import UserProfile

def _get_profile(key):
    try:
        u = User.objects.get(username='key:%s' % key)
    except ObjectDoesNotExist:
        return None
    try:
        p = u.profile.get()
    except ObjectDoesNotExist:
        return None
    return p

@login_required
def add_urlfilter(req, key, pattern):
    p = _get_profile(key)
    if not p:
        return HttpResponse("%s: key not found" % escape(key), status=404)
    if not p.add_urlfilter(req.user, escape(pattern)):
        return HttpResponse("Permission denied.", status=403)
    p.save()
    return HttpResponse("Added %s to %s." % (escape(pattern), p))

@login_required
def remove_urlfilter(req, key, pattern):
    p = _get_profile(key)
    if not p:
        return HttpResponse("%s: key not found" % escape(key))
    if not p.remove_urlfilter(req.user, escape(pattern)):
        return HttpResponse("Permission denied.", status=403)
    p.save()
    return HttpResponse("Removed %s from %s." % (escape(pattern), p))


@login_required
def add_tagconstraint(req, key, tag):
    p = _get_profile(key)
    if not p:
        return HttpResponse("%s: key not found" % escape(key))


@login_required
def remove_tagconstraint(req, key, tag):
    p = _get_profile(key)
    if not p:
        return HttpResponse("%s: key not found" % escape(key))
