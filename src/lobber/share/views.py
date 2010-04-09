import os
from datetime import datetime as dt
from hashlib import sha256
from random import getrandbits

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from lobber.settings import BASE_DIR, MEDIA_ROOT, LOGIN_URL, ANNOUNCE_URL, NORDUSHARE_URL, BASE_UI_URL, LOBBER_LOG_FILE
from lobber.share.models import Torrent, Tag, UserProfile
from forms import UploadForm, CreateKeyForm

from lobber.resource import Resource
import lobber.log
logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

def _create_key_user(creator, urlfilter, entitlements, expires=None):
    # FIXME: Do random.seed() somewhere.
    # FIXME: Is 256 bits of random data proper?
    # FIXME: Don't chop the digest!!!  Necessary for now, since
    # Djangos User class allows for max 30 characters user names.
    secret = sha256(str(getrandbits(256))).hexdigest()[:26]
    username = 'key:%s' % secret
    user = User.objects.create_user(username, 'nomail@dev.null', username)

    lst = map(lambda s: s.replace('$self', username), entitlements.split())
    entls = ' '.join(map(lambda e: 'user:%s:%s' % (creator.username, e), lst))
    profile = UserProfile(user=user,
                          creator=creator,
                          urlfilter=' '.join(urlfilter.split()),
                          entitlements=entls,
                          expiration_date=expires)
    profile.save()
    return secret
    
####################
# External functions, called from urls.py.

@login_required
def user_self(req):
    # FIXME: Move to api_user() -- this is GET user/U with
    # representation html.
    lst = []
    for t in Torrent.objects.all().order_by('-creation_date')[:40]:
        if t.auth(req.user.username, 'r') and t.expiration_date > dt.now():
            lst.append(t)
    return render_to_response('share/user.html', {'user': req.user,
                                                  'profile': req.user.profile.get(),
                                                  'torrents': lst})

@login_required
def gimme_url_for_reading_torrent(req, tid):
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return HttpResponse('Sorry, torrent %s not found'  % tid)
    key = _create_key_user(creator=req.user,
                           urlfilter='torrent/%s' % tid, # FIXME: Append '$'?
                           entitlements='user:%s:$self' % req.user.username)
    t.add_ace('user:%s:%s#r' % (req.user.username, key))
    #link = '%s/%s?lkey=%s' % (NORDUSHARE_URL, tid, key)
    link = '%s/torrent/%s.torrent?lkey=%s' % (NORDUSHARE_URL, t.hashval, key)
    return HttpResponse('Here\'s your link to share: <a href=%s>%s</a>' %
                        (link, link))

################################################################################
# RESTful API.

####################
# Keys.
@login_required
def api_keys(req):
    """
    GET ==> list keys
    POST ==> create key
    """
    def _list(user):
        lst = []
        for p in UserProfile.objects.filter(creator=user):
            if p.expiration_date and p.expiration_date <= dt.now():
                continue
            if not p.user.username.startswith('key:'):
                continue
            lst.append(p)
        return lst

    d = {'user': req.user}
        
    if req.method == 'GET':
        d.update({'keys': _list(req.user)})
        response = render_to_response('share/keys.html', d)
    elif req.method == 'POST':
        form = CreateKeyForm(req.POST)
        if form.is_valid():
            _create_key_user(req.user,
                             form.cleaned_data['urlfilter'],
                             form.cleaned_data['entitlements'],
                             form.cleaned_data['expires'])
            d.update({'keys': _list(req.user)})
            response = render_to_response('share/keys.html', d)
        else:
            response = render_to_response('share/create_key.html',
                                          {'form': CreateKeyForm(),
                                           'user': req.user})
    return response

@login_required
def api_key(req, inst):
    """
    GET ==> get key
    DELETE ==> delete key
    """
    response = HttpResponse('NYI: not yet implemented')
    return response

def key_form(req):
    return render_to_response('share/create_key.html',
                              {'form': CreateKeyForm(),
                               'user': req.user})
