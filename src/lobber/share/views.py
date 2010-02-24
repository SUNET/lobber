import os
from datetime import datetime as dt

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from settings import BASE_DIR, MEDIA_ROOT, LOGIN_URL, ANNOUNCE_URL, NORDUSHARE_URL
from forms import UploadForm, UploadTorrentForm, UploadAppletForm
from lobber.share.models import Torrent, Tag, Key, ACL

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
    
def list_torrents(max=40):
    lst = []
    for t in Torrent.objects.all().order_by('-creation')[:max]:
        if t.published and t.expiration > dt.now():
            lst.append(t)
    return lst

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
    t = Torrent(owner = req.user,
                name = form.cleaned_data['name'],
                published = form.cleaned_data['published'],
                expiration = form.cleaned_data['expires'],
                data = '%s.torrent' % torrent_hash,
                hashval = torrent_hash)
    t.save()
    add_hash_to_whitelist(torrent_hash)
    return HttpResponseRedirect('../%s' % t.id)

####################
def torrent_list(req):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s?next=%s' % (LOGIN_URL, req.path))
    return render_to_response('share/index.html',
                              {'torrents': list_torrents(),
				'user': req.user})

def upload(req):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    d = {'sessionid': req.session.session_key,
         'announce_url': ANNOUNCE_URL,
         'baseurl': NORDUSHARE_URL,
         'apiurl': '%s/ulform/' % NORDUSHARE_URL} # ==> upload_form() via urls.py.
    d.update({'form': UploadAppletForm(d)})
    return render_to_response('share/launch.jnlp', d,
                              mimetype='application/x-java-jnlp-file')

def upload_form(req):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    if req.method == 'POST':          # User posted data -- handle it.
        form = UploadForm(req.POST, req.FILES)
        if form.is_valid():
            d = {'name': form.cleaned_data['name'],
                 'published': form.cleaned_data['published'],
                 'expires': form.cleaned_data['expires'],
                 'announce_url': ANNOUNCE_URL}
            d.update({'form': UploadTorrentForm(d)})
            return render_to_response('share/upload-torrent.html', d)
    else:
        form = UploadForm()
    return render_to_response('share/upload-torrent.html', {'form': form})
        
# This is ghetto, having a separate function for each upload type.
# It's only temporary!  I swear!
def torrent_add1(req):
    if req.method == 'POST':          # User posted data -- handle it.
        if not req.user.is_authenticated():
            return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
        form = UploadTorrentForm(req.POST, req.FILES)
        if form.is_valid():
            return _store_torrent(req, form)
    else:                               # Render an empty form.
        form = UploadForm()
    return render_to_response('share/upload.html', {'form': form})

def torrent_add2(req):
    if req.method == 'POST':          # User posted data -- handle it.
        if not req.user.is_authenticated():
            return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
        form = UploadAppletForm(req.POST, req.FILES)
        if form.is_valid():
            return _store_torrent(req, form)
    else:                               # Render an empty form.
        form = UploadForm()
    return render_to_response('share/upload.html', {'form': form})


def torrent_view(req, handle_id):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    t = Torrent.objects.get(id__exact = int(handle_id))
    return render_to_response('share/torrent.html', {'torrent': t})

def torrent_get(req, tfile):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    fn = '%s/torrents/%s' % (MEDIA_ROOT, tfile)
    response = HttpResponse(FileWrapper(file(fn)), content_type='application/x-bittorrent')
    response['Content-Length'] = os.path.getsize(fn)
    response['Content-Disposition'] = 'filename=%s.torrent' % tfile # FIXME: Find Torrent object and use .name instead.
    return response

# def login(req):
#     if req.method != 'POST':
#         return render_to_response('share/login.html', {'form': LoginForm()})
#     else:
#         form = LoginForm(req.POST)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             pw = form.cleaned_data['pw']
#             print username, pw
#             user = authenticate(username=username, passsword=pw)
#             if not user:
#                 return HttpResponse("bad username or password")
#             else:
#                 if user.is_active:
#                     login(req, user)
#                     return HttpResponseRedirect('/') # FIXME0: Redirect to "my torrents".  FIXME1: Find out where user came from and redirect there.
#                 else:
#                     return HttpResponse("account inactive")

def user_view(req):
    if not req.user.is_authenticated():
        return HttpResponseRedirect('%s/?next=%s' % (LOGIN_URL, req.path))
    MAX = 40
    lst = []
    for t in Torrent.objects.all().order_by('-creation')[:MAX]:
        if t.owner == req.user and t.expiration > dt.now():
            lst.append(t)
    return render_to_response('share/user.html',
                              {'user': req.user,
                               'torrents': lst})
