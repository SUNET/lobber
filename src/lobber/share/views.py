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

from lobber.settings import BASE_DIR, MEDIA_ROOT, LOGIN_URL, ANNOUNCE_URL, NORDUSHARE_URL, BASE_UI_URL
from lobber.share.models import Torrent, Tag, UserProfile
from forms import UploadForm, CreateKeyForm

####################
# Helper functions. FIXME: Move to some other file.
from BitTorrent.bencode import bdecode, bencode
from hashlib import sha1
def do_hash(data):
    cont = bdecode(data)
    info = cont['info']
    return sha1(bencode(info)).hexdigest()

def add_hash_to_whitelist(thash):
    """
    Add THASH to tracker whitelist file and send signal HUP to the
    tracker.
    """
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
    # FIXME: Move to api_torrents() -- this is (part of) POST torrent/
    # (create).
    """
    Store torrent file in the file system and add its hash to the
    trackers whitelist.
    """
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
# External functions, called from urls.py.

@login_required
def upload(req):
    d = {'sessionid': req.session.session_key,
         'announce_url': ANNOUNCE_URL,
         'baseurl': BASE_UI_URL,
         'apiurl': '%s/ulform/' % NORDUSHARE_URL} # ==> upload_form() via urls.py.
    return render_to_response('share/launch.jnlp', d,
                              mimetype='application/x-java-jnlp-file')

@login_required
def upload_form(req):
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
        
@login_required
def torrent_view(req, handle_id):
    # FIXME: Move to api_torrents() -- this is GET torrent/T with
    # representation html.
    t = Torrent.objects.get(id__exact = int(handle_id))
    return render_to_response('share/torrent.html', {'torrent': t})

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

################################################################################
# RESTful API.

####################
# Torrents.
@login_required
def api_torrents(req):
    """
    GET ==> list torrents
    POST ==> create torrent
    """
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

@login_required
def api_torrent(req, inst):
    """
    GET ==> get torrent
    ??? PUT/POST ==> update torrent ???
    DELETE ==> delete torrent
    """
    response = HttpResponse('NYI: not yet implemented')

    fn = '%s/torrents/%s' % (MEDIA_ROOT, inst)
    if req.method == 'GET':
        # FIXME: Do this only if representation is raw.
        response = HttpResponse(FileWrapper(file(fn)), content_type='application/x-bittorrent')
        response['Content-Length'] = os.path.getsize(fn)
        # FIXME: Find Torrent object and use .name instead of filename.
        response['Content-Disposition'] = 'filename=%s.torrent' % inst
    return response

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
            lst.append(p[4:])
        return lst

    d = {'user': req.user}
        
    if req.method == 'GET':
        d.update({'keys': _list(req.user)})
        response = render_to_response('share/keys.html', d)
    elif req.method == 'POST':
        form = CreateKeyForm(req.POST)
        if form.is_valid():
            # FIXME: Do random.seed() somewhere.
            # FIXME: Is 256 bits of random data proper?
            # FIXME: Don't chop the digest!!!  Necessary for now,
            # since Djangos User class allows for max 30 characters
            # user names.
            user = User(username='key:%s' % sha256(str(getrandbits(256))).hexdigest()[:26],
                        password='')
            user.save()
            urlfilter = ' '.join(form.cleaned_data['urlfilter'].split())
            entls = ' '.join(map(lambda e: 'user:%s:%s' % (req.user.username, e),
                                 form.cleaned_data['entitlements'].split()))
            profile = UserProfile(user=user,
                                  creator=req.user,
                                  urlfilter=urlfilter,
                                  entitlements=entls,
                                  expiration_date=form.cleaned_data['expires'])
            profile.save()
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
