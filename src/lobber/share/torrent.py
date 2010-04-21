import os
from datetime import datetime as dt

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from lobber.multiresponse import respond_to, make_response_dict
from lobber.settings import TORRENTS, ANNOUNCE_URL, NORDUSHARE_URL, BASE_UI_URL, LOBBER_LOG_FILE

from lobber.resource import Resource
import lobber.log
from lobber.share.forms import UploadForm
from lobber.share.models import Torrent
from lobber.notify import notify
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
    t = Torrent(acl='user:%s#w' % req.user.username,
                creator=req.user,
                name=torrent_name,
                description=form.cleaned_data['description'],
                expiration_date=form.cleaned_data['expires'],
                data='%s.torrent' % torrent_hash,
                hashval=torrent_hash)
    t.save()
    notify("/torrent/new", torrent_hash);
    return t.id
    
####################
# External functions, called from urls.py.

def welcome(req):
    return HttpResponseRedirect("/torrent/")

@login_required
def delete_torrent(req, tid):
    raise

@login_required
def upload_jnlp(req):
    d = {'sessionid': req.session.session_key,
         'announce_url': ANNOUNCE_URL,
         'baseurl': BASE_UI_URL,
         'apiurl': '%s/torrent/new/' % NORDUSHARE_URL} # ==> upload_form() via urls.py.
    return render_to_response('share/launch.jnlp', d,
                              mimetype='application/x-java-jnlp-file')

def exists(req, inst):
    r = HttpResponse(status=200);
    r['Cache-Control'] = 'max-age=5'
    try:
        t = Torrent.objects.get(hashval=inst)
        r.content = t.hashval
    except ObjectDoesNotExist:
        r.status_code = 404
    return r;

class TorrentViewBase(Resource):
    """
    POST and PUT creates/updates a torrent
    """

    @login_required
    def post(self, req):
        form = UploadForm(req.POST, req.FILES)
        if form.is_valid():
            tid = _store_torrent(req, form)
            return HttpResponseRedirect('/torrent/#%d' % tid)
        else:
            logger.info("upload_form: received invalid form")

    @login_required
    def put(self, req):
        form = UploadForm(req.POST, req.FILES)
        if form.is_valid():
            tid = _store_torrent(req, form)
            return HttpResponseRedirect('/torrent/#%d' % tid)
        else:
            logger.info("upload_form: received invalid form")

class TorrentForm(TorrentViewBase):

    @login_required
    def get(self, req):
        return render_to_response('share/upload-torrent.html',
                                   make_response_dict(req,{'form': UploadForm()}))

def _torrent_file_response(dict):
    t = dict.get('torrent')
    f = t.file()
    response = HttpResponse(FileWrapper(f), content_type='application/x-bittorrent')
    response['Content-Length'] = os.path.getsize(f.name)
    response['Content-Disposition'] = 'filename=%s.torrent' % t.name
    return response

class TorrentView(TorrentViewBase):

    def _list(self, user, max=40):
        lst = []
        for t in Torrent.objects.all().order_by('-creation_date')[:max]:
            if t.authz(user, 'r') and t.expiration_date > dt.now():
                lst.append(t)
        return lst

    @login_required
    def get(self, request, inst=None):
        if not inst:
            return render_to_response('share/index.html',
                                      make_response_dict(request,{'torrents': self._list(request.user)}))

        try:
            t = Torrent.objects.get(hashval=inst)
        except ObjectDoesNotExist:
            return render_to_response('share/index.html', make_response_dict(request,{'error': "No such torrent: %s" % inst}))

        return respond_to(request,
                          {'text/html': 'share/torrent.html',
                           'application/x-bittorrent': lambda dict: _torrent_file_response(dict)},
                          {'torrent': t})
