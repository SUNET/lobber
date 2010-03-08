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

####################
# Helper functions. FIXME: Move to some other file.
from BitTorrent.bencode import bdecode, bencode
from hashlib import sha1
def _torrent_info(data):
    """
    Return (name, hash) of torrent file.
    """
    info = bdecode(data)['info']
    return info['name'], sha1(bencode(info)).hexdigest()

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
        """
        Store torrent file in the file system and add its hash to the
        trackers whitelist.
        """
        torrent_file = req.FILES['file']
        # FIXME: Limit amount read and check length of returned data.
        torrent_file_content = torrent_file.read()
        torrent_file.close()
        torrent_name, torrent_hash = _torrent_info(torrent_file_content)
        name_on_disk = '%s/torrents/%s' % (MEDIA_ROOT, '%s.torrent' % torrent_hash)
        f = file(name_on_disk, 'w')
        f.write(torrent_file_content)
        f.close()
        t = Torrent(acl = 'user:%s#w' % req.user.username,
                    creator = req.user,
                    name = torrent_name,
                    description = form.cleaned_data['description'],
                    expiration_date = form.cleaned_data['expires'],
                    data = '%s.torrent' % torrent_hash,
                    hashval = torrent_hash)
        t.save()
        add_hash_to_whitelist(torrent_hash)
        return t.id
    
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
def upload(req):
    d = {'sessionid': req.session.session_key,
         'announce_url': ANNOUNCE_URL,
         'baseurl': BASE_UI_URL,
         'apiurl': '%s/ulform/' % NORDUSHARE_URL} # ==> upload_form() via urls.py.
    return render_to_response('share/launch.jnlp', d,
                              mimetype='application/x-java-jnlp-file')

@login_required
def torrent_view(req, tid):
    # FIXME: Move to api_torrents() -- this is GET torrent/T with
    # representation html.
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return HttpResponse(
            'Sorry, torrent %s not found<p><a href="%s">Start page</a>' %
            (tid, NORDUSHARE_URL))
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
# Torrents.

class TorrentViewBase(Resource):

    @login_required
    def post(self,req):
        form = UploadForm(req.POST, req.FILES)
        if form.is_valid():
           tid = _store_torrent(req,form)
           return HttpResponseRedirect('../%s' % tid)
        else:
           logger.info("upload_form: received invalid form")

    @login_required
    def put(self,req):
        form = UploadForm(req.POST, req.FILES)
        if form.is_valid():
           tid = _store_torrent(req,form)
           return HttpResponseRedirect('../%s' % tid)
        else:
           logger.info("upload_form: received invalid form")

class TorrentsView(TorrentViewBase):
    """
    GET ==> list torrents
    PUT ==> create torrent
    """
    
    def _list(self,user,max=40):
        lst = []
        for t in Torrent.objects.all().order_by('-creation_date')[:max]:
            if t.auth(user.username, 'r') and t.expiration_date > dt.now():
                lst.append(t)
        return lst
    
    @login_required
    def get(self,req):
        return render_to_response('share/index.html',
                                  {'torrents': self._list(req.user),
                                   'user': req.user})

class TorrentForm(TorrentViewBase):

    @login_required
    def get(self,req):
        return render_to_response('share/upload-torrent.html',
                                   {'announce_url': ANNOUNCE_URL,
                                    'user': req.user,
                                    'form': UploadForm()})

class TorrentView(TorrentViewBase):
     
    @login_required
    def get(self,request,inst):
        response = HttpResponse('NYI: not yet implemented')
        fn = '%s/torrents/%s' % (MEDIA_ROOT, inst)
	f = None
        try:
            f = file(fn)
        except IOError, e:
            if e[0] == 2:               # ENOENT
                response = HttpResponseRedirect(NORDUSHARE_URL)
            else:
                raise
        if f is not None:
            response = HttpResponse(FileWrapper(f), content_type='application/x-bittorrent')
            response['Content-Length'] = os.path.getsize(fn)

            fname = inst
            t = None
            try:
                t = Torrent.objects.get(hashval=inst)
            except ObjectDoesNotExist:
                pass
            except Torrent.MultipleObjectsReturned:
                pass
            if t:
                fname = t.name
                response['Content-Disposition'] = 'filename=%s.torrent' % fname
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
