import os
import sys
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
from lobber.multiresponse import respond_to
from lobber.settings import BASE_DIR, TORRENTS, LOGIN_URL, ANNOUNCE_URL, NORDUSHARE_URL, BASE_UI_URL, LOBBER_LOG_FILE
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
    name_on_disk = '%s/%s' % (TORRENTS, '%s.torrent' % torrent_hash)
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
    
####################
# External functions, called from urls.py.

def welcome(req):
   return HttpResponseRedirect("/torrent/")

@login_required
def delete_torrent(req,tid):
   raise

@login_required
def upload_jnlp(req):
    d = {'sessionid': req.session.session_key,
         'announce_url': ANNOUNCE_URL,
         'baseurl': BASE_UI_URL,
         'apiurl': '%s/ulform/' % NORDUSHARE_URL} # ==> upload_form() via urls.py.
    return render_to_response('share/launch.jnlp', d,
                              mimetype='application/x-java-jnlp-file')

class TorrentViewBase(Resource):
    """
    POST and PUT creates/updates a torrent
    """

    @login_required
    def post(self,req):
        form = UploadForm(req.POST, req.FILES)
        if form.is_valid():
           tid = _store_torrent(req,form)
           return HttpResponseRedirect('/torrent/#%d' % tid)
        else:
           logger.info("upload_form: received invalid form")

    @login_required
    def put(self,req):
        form = UploadForm(req.POST, req.FILES)
        if form.is_valid():
           tid = _store_torrent(req,form)
           return HttpResponseRedirect('/torrent/#%d' % tid)
        else:
           logger.info("upload_form: received invalid form")

class TorrentForm(TorrentViewBase):

    @login_required
    def get(self,req):
        return render_to_response('share/upload-torrent.html',
                                   {'announce_url': ANNOUNCE_URL,
                                    'user': req.user,
                                    'form': UploadForm()})

def _torrent_file_response(dict):
    t = dict.get('torrent')
    f = t.file()
    response = HttpResponse(FileWrapper(f), content_type='application/x-bittorrent')
    response['Content-Length'] = os.path.getsize(f.name)
    response['Content-Disposition'] = 'filename=%s.torrent' % t.name
    return response

class TorrentView(TorrentViewBase):

    def _list(self,user,max=40):
        lst = []
        for t in Torrent.objects.all().order_by('-creation_date')[:max]:
            if t.auth(user.username, 'r') and t.expiration_date > dt.now():
                lst.append(t)
        return lst

    @login_required
    def get(self,request,inst=None):
        if not inst:
	   return render_to_response('share/index.html',
                                     {'torrents': self._list(request.user),'user': request.user})

        try:
           t = Torrent.objects.get(hashval=inst)
        except ObjectDoesNotExist:
           return render_to_response('share/index.html',{'user': request.user, 'error': "No such torrent: %s" % inst})

        f = t.file
        return respond_to(request,
                          {'text/html': 'share/torrent.html',
                           'application/x-bittorrent': lambda dict: _torrent_file_response(dict)},
                          {'torrent': t})
