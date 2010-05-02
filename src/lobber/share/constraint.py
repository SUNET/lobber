from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils.html import escape
from django.contrib.auth.models import User
from lobber.share.models import UserProfile

def get_profile(key):
    try:
        u = User.objects.get(username='key:%s' % key)
    except ObjectDoesNotExist:
        return None
    try:
        p = u.profile.get()
    except ObjectDoesNotExist:
        return None
    return p


def add_constraint(req, key, constraint, fun):
    p = get_profile(key)
    if not p:
        return HttpResponse("%s: key not found" % escape(key), status=404)
    if not fun(p, req.user, escape(constraint)):
        return HttpResponse("Permission denied.", status=403)
    p.save()
    return HttpResponse("Added %s to %s." % (escape(constraint), p))

def remove_constraint(req, key, constraint, fun):
    p = get_profile(key)
    if not p:
        return HttpResponse("%s: key not found" % escape(key))
    if not fun(p, req.user, escape(constraint)):
        return HttpResponse("Permission denied.", status=403)
    p.save()
    return HttpResponse("Removed %s from %s." % (escape(constraint), p))


@login_required
def add_urlfilter(req, key, pattern):
    return add_constraint(req, key, pattern, UserProfile.add_urlfilter)

@login_required
def remove_urlfilter(req, key, pattern):
    return remove_constraint(req, key, pattern, UserProfile.remove_urlfilter)

@login_required
def add_tagconstraint(req, key, tag):
    return remove_constraint(req, key, tag, UserProfile.add_tagconstraint)

@login_required
def remove_tagconstraint(req, key, tag):
    return remove_constraint(req, key, tag, UserProfile.remove_tagconstraint)
