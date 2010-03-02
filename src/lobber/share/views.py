import os
from datetime import datetime as dt
from hashlib import sha256
from random import getrandbits

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from lobber.settings import BASE_DIR, MEDIA_ROOT, LOGIN_URL, ANNOUNCE_URL, NORDUSHARE_URL, BASE_UI_URL
from lobber.share.models import Torrent, Tag
from forms import UploadForm

####################
# Helper functions. FIXME: Move to some other file.
from BitTorrent.bencode import bdecode, bencode
from hashlib import sha1
def do_hash(data):
    cont = bdecode(data)
    info = cont['info']
    return sha1(bencode(info)).hexdigest()

def add_hash_to_whitelist(thash):
    # Append hash to whitelist file.
    wlf = file('%s/%s' % (BASE_DIR, 'tracker/whitelist'), 'a')
    wlf.write(thash + '\n')
    wlf.close()
    # Read PID file.
    pidf = file('%s/%s' % (BASE_DIR, 'tracker/pid'), 'r')
    pid = int(pidf.read())
    pidf.close()
    # HUP tracker.
    os.kill(pid, 1)
    
def _store_torrent(req, form):
    # Store torrent file in the file system and add its hash
    # to the trackers whitelist.
    torrent_file = req.FILES['file']
    torrent_file_content = torrent_file.read()
    torrent_hash = do_hash(torrent_file_content)
    name_on_disk = '%s/torrents/%s' % (MEDIA_ROOT, '%s.torrent' % torrent_hash)
    f = file(name_on_disk, 'w')
    f.write(torrent_file_content)
    f.close()
    t = Torrent(acl = 'user:%s#w' % req.user.username,
                creator = req.user,
                name = form.cleaned_data['name'],
                expiration_date = form.cleaned_data['expires'],
                data = '%s.torrent' % torrent_hash,
                hashval = torrent_hash)
    t.save()
    add_hash_to_whitelist(torrent_hash)
    # FIXME: Go to user page, with newly created torrent highlighted.
    return HttpResponseRedirect('../%s' % t.id)

####################
def upload(req):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    d = {'sessionid': req.session.session_key,
         'announce_url': ANNOUNCE_URL,
         'baseurl': BASE_UI_URL,
         'apiurl': '%s/ulform/' % NORDUSHARE_URL} # ==> upload_form() via urls.py.
    return render_to_response('share/launch.jnlp', d,
                              mimetype='application/x-java-jnlp-file')

def upload_form(req):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    if req.method == 'POST':          # User posted data -- handle it.
        form = UploadForm(req.POST, req.FILES)
        if form.is_valid():
            return _store_torrent(req, form)
    else:
        form = UploadForm()
    return render_to_response('share/upload-torrent.html',
                              {'announce_url': ANNOUNCE_URL,
                               'user': req.user,
                               'form': form})
        
def torrent_view(req, handle_id):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    t = Torrent.objects.get(id__exact = int(handle_id))
    return render_to_response('share/torrent.html', {'torrent': t})

def user_self(req):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    MAX = 40
    lst = []
    for t in Torrent.objects.all().order_by('-creation_date')[:MAX]:
        if t.auth(req.user.username, 'r') and t.expiration_date > dt.now():
            lst.append(t)
    return render_to_response('share/user.html', {'user': req.user,
                                                  'profile': req.user.profile.get(),
                                                  'torrents': lst})

################################################################################
# RESTful API.

####################
# Torrents.
def api_torrents(req):
    """
    GET ==> list torrents
    PUT/POST ==> create torrent
    """
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    response = HttpResponse('NYI: not yet implemented')

    def _list(user, max=40):
        lst = []
        for t in Torrent.objects.all().order_by('-creation_date')[:max]:
            if t.auth(user.username, 'r') and t.expiration_date > dt.now():
                lst.append(t)
        return lst

    if req.method == 'GET':
        response = render_to_response('share/index.html',
                                      {'torrents': _list(req.user),
                                       'user': req.user})
    return response

def api_torrent(req, inst):
    """
    GET ==> get torrent
    ??? PUT/POST ==> update torrent ???
    DELETE ==> delete torrent
    """
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    response = HttpResponse('NYI: not yet implemented')

    fn = '%s/torrents/%s' % (MEDIA_ROOT, inst)
    if req.method == 'GET':
        response = HttpResponse(FileWrapper(file(fn)), content_type='application/x-bittorrent')
        response['Content-Length'] = os.path.getsize(fn)
        # FIXME: Find Torrent object and use .name instead of filename.
        response['Content-Disposition'] = 'filename=%s.torrent' % inst
    return response

####################
# Keys.
def api_keys(req):
    """
    GET ==> list keys
    POST ==> create key
    """
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))

    def _list(user):
        lst = []
        for p in UserProfile.objects.filter(creator=user):
            if p.expiration_date > dt.now():
                lst.append(p)
        return lst

    d = {'keys': _list(),
         'user': req.user})
    response = render_to_response('share/keys.html', d)
        
    if req.method == 'GET':
        pass                            # Default response is fine.
    elif req.method == 'POST':
        form = CreateKeyForm(req.POST)
        if form.is_valid():
            # FIXME: Do random.seed() somewhere.
            # FIXME: Is 256 bits of random data proper?
            user = User(username='key:%s' % sha256(getrandbits(256)),
                        password='')
            user.save()
            profile = Profile(user=user,
                              creator=req.user,
                              urlfilter=form.cleaned_data['urlfilter'],
                              entitlements=form.cleaned_data['entitlements'],
                              expires=form.cleaned_data['expires'])
            profile.save()
            d.update({'keys': _list()})
        else:
            response = render_to_response('share/create_key.html'
                                          {'form': CreateKeyForm(),
                                           'user': req.user})
    return response

def api_key(req, inst):
    """
    GET ==> get key
    DELETE ==> delete key
    """
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    response = HttpResponse('NYI: not yet implemented')
    return response

def key_form(req):
    return render_to_response('share/create_key.html'
                              {'form': CreateKeyForm(),
                               'user': req.user})
