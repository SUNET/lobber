from datetime import datetime as dt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect,HttpResponseForbidden,\
    HttpResponseNotFound, HttpResponseNotAllowed, HttpResponse,\
    HttpResponseBadRequest
from lobber.userprofile.forms import CreateKeyForm
from lobber.settings import LOBBER_LOG_FILE
from django.contrib.auth.models import User, Group
from lobber.multiresponse import respond_to, make_response_dict, json_response
import lobber.log
from django.shortcuts import get_object_or_404, render_to_response
from lobber.userprofile.models import UserProfile, user_profile
from django.core.exceptions import ObjectDoesNotExist
import binascii
from lobber.share.models import Torrent
from django.utils.html import escape

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

def _list_keys(user):
        lst = []
        for p in UserProfile.objects.filter(creator=user).order_by('-id'):
            if p.expiration_date and p.expiration_date <= dt.now():
                continue
            if not p.user.username.startswith('key:'):
                continue
            lst.append(p)
        return lst

@login_required
def removekey(request,key):
    keyuser = get_object_or_404(User,username="key:%s" % key)
    keyprofile = user_profile(keyuser)
    if keyprofile.creator.username != request.user.username:
        return HttpResponseForbidden("That is not your key!")
    
    keyprofile.delete()
    keyuser.delete()
    return HttpResponseRedirect(reverse('lobber.userprofile.views.listkeys'))

@login_required
def addkey(request):
    if request.method == 'POST':
        form = CreateKeyForm(request.POST)
        form.fields['groups'].choices = [(g.id,g.name) for g in request.user.groups.all()]
        if form.is_valid():
            secret = create_key_user(request.user,
                                     form.cleaned_data['urlfilter'] or "^.*$",
                                     "", #TODO: tagconstraints
                                     form.cleaned_data['groups'],
                                     form.cleaned_data['expires'])
            return respond_to(request,
                              {'application/json': json_response(secret),
                               'text/html': HttpResponseRedirect("/user/key")})
    else:        
        form = CreateKeyForm()
        form.fields['groups'].choices = [(g.id,g.name) for g in request.user.groups.all()]
    
    return respond_to(request,
                      {'application/json': HttpResponseBadRequest("invalid request"),
                       'text/html': 'userprofile/addkey.html'},{'form': form})

@login_required
def listkeys(request):
    return respond_to(request,
                      {"text/html": 'userprofile/keys.html'},{'keys': _list_keys(request.user)})


def create_key_user_profile(creator, urlfilter, tagconstraints, groups, expires=None):
    """
    Create a user profile named key:<random text>.

    Also, '$self' is substituted for the name of the newly created key-user.
    """
    creator_profile = None
    try:
        creator_profile = creator.profile.get()
    except ObjectDoesNotExist:
        pass
    if not creator_profile:
        return None

    secret = binascii.hexlify(open('/dev/urandom').read(13))
    username = 'key:%s' % secret

    user = User.objects.create_user(username, 'nomail@dev.null', username)
    urlfilter = ' '.join(urlfilter.split())
    tagconstraints = ' '.join(tagconstraints.split())

    profile = UserProfile(user=user,
                          creator=creator,
                          urlfilter=urlfilter,
                          tagconstraints=tagconstraints,
                          entitlements="",
                          expiration_date=expires)
    profile.save()

    for group in groups:
        g = Group.objects.get(pk=group[0])
        user.groups.add(g)

    return profile

def create_key_user(creator, urlfilter, tagconstraints, entitlements, expires=None):
    profile = create_key_user_profile(creator, urlfilter, tagconstraints, entitlements, expires)
    return profile.get_username()

@login_required
def user_self(req):
    lst = []
    for t in Torrent.objects.all().order_by('-creation_date')[:40]:
        if t.authz(req.user, 'r') and t.expiration_date > dt.now():
            lst.append(t)

    return render_to_response('userprofile/user.html', 
                              make_response_dict(req,{'torrents': lst}))

@login_required
def ace_subjects(req):
    term = req.GET['term']
    subjects = []
    if term:
        subjects.append({'label': 'Anyone','id': 0,'type':'anyone'})
        for g in Group.objects.filter(name__contains=term):
            subjects.append({'label': "Members of '%s'" % g.name,'id':g.id,'type':'group'}) 
        for u in User.objects.filter(username__contains=term):
            subjects.append({'label': u.username,'id':u.id,'type':'group'}) 
        
    return json_response(subjects)

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
        return HttpResponseNotFound("%s: key not found" % escape(key))
    if not fun(p, req.user, escape(constraint)):
        return HttpResponseNotAllowed("Permission denied.")
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
