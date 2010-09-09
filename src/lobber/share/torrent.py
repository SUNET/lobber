import os
import httplib
from datetime import datetime as dt

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User

from tagging.models import Tag, TaggedItem

from lobber.multiresponse import respond_to, make_response_dict, json_response
from lobber.settings import TORRENTS, ANNOUNCE_URL, NORDUSHARE_URL, BASE_UI_URL, LOBBER_LOG_FILE, TRACKER_ADDR
from lobber.resource import Resource
import lobber.log
from lobber.share.forms import UploadForm
from lobber.share.models import Torrent
from lobber.notify import notifyJSON
from django.utils.http import urlencode
from django import forms
from lobber.share.forms import formdict

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

####################
# Helper functions. FIXME: Move to some other file.
from deluge.bencode import bdecode, bencode
from deluge.metafile import make_meta_file
from hashlib import sha1

def _torrent_info(data):
    """
    Return (name, hash) of torrent file.
    """
    info = bdecode(data)['info']
    return info['name'], sha1(bencode(info)).hexdigest()

def _create_torrent(filename, announce_url, target_file, comment=None):
    make_meta_file(filename, announce_url, 2 ** 18, comment=comment, target=target_file)

def _store_torrent(req, form):
    """
    Check if req.user already has the torrent file (req.FILES) in the
    database.  Note that the identity of a torrent is Torrent.hashval.

    If the torrent is already in the system, update the entry with new
    meta data (name, description, expiration date).

    If this is a new torrent (for this user), create a new Torrent
    object in the database and store the torrent file in the file
    system.
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

    acl = []
    publicAccess = form.cleaned_data['publicAccess']
    if publicAccess:
        acl.append("#r")
    acl.append('user:%s#w' % req.user.username)
    acl.append('urn:x-lobber:storagenode#r')

    t = None
    notification = None
    try:
        t = Torrent.objects.get(hashval=torrent_hash)
    except ObjectDoesNotExist:
        t = Torrent(acl=" ".join(acl),
                    creator=req.user,
                    name=torrent_name,
                    description=form.cleaned_data['description'],
                    expiration_date=form.cleaned_data['expires'],
                    data='%s.torrent' % torrent_hash,
                    hashval=torrent_hash)
        notification = '/torrent/add'
    except MultipleObjectsReturned, e:
        # Pathological case that can happen with corrupt (or old) database.
        # FIXME: Handle error case.
        pass
    else:                            # Found torrent, update database.
        assert(t.data == '%s.torrent' % torrent_hash)
        assert(t.hashval == torrent_hash)
        t.name = torrent_name
        t.description = form.cleaned_data['description']
        t.expiration_date = form.cleaned_data['expires']
        notification = '/torrent/update'

    if t:
        t.save()
        notifyJSON(notification, t.id)

    return t
    
def _urlesc(s):
    r = ''
    for n in range(0, len(s), 2):
        r += '%%%s' % s[n:n+2].upper()
    return r

def _prefetch_existlink(hash):
    url = '/announce?info_hash='+_urlesc(hash)
    #print 'DEBUG: prefetching %s from %s' % (url, TRACKER_ADDR)
    try:
        httplib.HTTPConnection(TRACKER_ADDR).request('GET', url)
    except:
        pass

def find_torrents(user, args, max=40):
    """Search for torrents for which USER has read access.
    Filter on certain properties found in ARGS.

    https://.../torrent/?txt=STRING&tag=STRING&user=STRING
    """
    q = Torrent.objects.filter(expiration_date__gt=dt.now()).order_by('-creation_date')
    empty_set = Torrent.objects.in_bulk([])

    for e, vals in args:            # args=(field, [search strings])
        if e == 'user':
            try:
                u = User.objects.get(username=vals[0])
            except ObjectDoesNotExist:
                q = empty_set
                break
            q = q.filter(creator=u)
        elif e == 'txt':
            for re in vals:
                q = q.filter(description__iregex=re) | q.filter(name__iregex=re)
        elif e == 'tag':
            for val in vals:
                try:
                    tag = Tag.objects.get(name=val)
                except ObjectDoesNotExist:
                    q = empty_set
                    break
                q = TaggedItem.objects.get_by_model(q, tag)
        
    return filter(lambda t: t.authz(user, 'r'), q)[:max]
    

def _torrent_file_response(dict):
    t = dict.get('torrent')
    f = t.file()
    response = HttpResponse(FileWrapper(f), content_type='application/x-bittorrent')
    response['Content-Length'] = os.path.getsize(f.name)
    response['Content-Disposition'] = 'filename=%s.torrent' % t.name
    return response

def _torrentlist(request, torrents):
    return respond_to(request,
                      {'text/html': 'share/index.html',
                       'application/rss+xml': 'share/rss2.xml',
                       'text/rss': 'share/rss2.xml',
                       'application/json': json_response([{'label': t.name,'link': "/torrent/%d" % (t.id)} for t in torrents])},
                      {'torrents': torrents, 'title': 'Search result',
                       'description': 'Search result'})

def torrentdict(request,t,forms=None):
    if not forms:
        forms = formdict()
    tags = map(lambda t: t.name,t.readable_tags(request.user))
    acl = t.get_acl(request.user)
    return {'torrent': t, 
            'forms': forms, 
            'tags': tags, 
            'acl': acl,
            'read': t.authz(request.user,'r'), 
            'write': t.authz(request.user,'w'), 
            'delete': t.authz(request.user,'d')}

####################
# External functions, called from urls.py.

def welcome(req):
    return HttpResponseRedirect("/torrent/")

@login_required
def remove_torrent(request, tid):
    t = get_object_or_404(Torrent,pk=tid)
    t.remove()
    return respond_to(request,
                      {'application/json': json_response(tid),
                       'text/html': HttpResponseRedirect("/torrent")})

@login_required
def scrape(request,inst):
    t = None
    try:
        t = Torrent.objects.get(id=inst)
    except ObjectDoesNotExist:
        return None
    
    url = '/scrape/?info_hash='+t.eschash()
    dict = {}
    try:
        c = httplib.HTTPConnection(TRACKER_ADDR)
        c.request('GET', url)
        txt = c.getresponse().read()
        response = bdecode(txt)
        dict = response['files'][t.hashval.decode('hex')]
    except Exception,e:
        pass
    
    return json_response(dict)

@login_required
def upload_jnlp(req):
    d = {'sessionid': req.session.session_key,
         'announce_url': ANNOUNCE_URL,
         'baseurl': BASE_UI_URL,
         'apiurl': '%s/torrent/add/' % NORDUSHARE_URL} # ==> upload_form() via urls.py.
    return render_to_response('share/launch.jnlp', d,
                              mimetype='application/x-java-jnlp-file')

def exists(req, inst):
    r = HttpResponse(status=200);
    r['Cache-Control'] = 'max-age=1800' # seconds
    try:
        t = Torrent.objects.get(hashval=inst)
        r.content = t.hashval
    except ObjectDoesNotExist:
        r.status_code = 404
        r['Cache-Control'] = 'max-age=2'
    except MultipleObjectsReturned:
        pass                            # Ok.
    return r;

## TODO: This class stuff wasn't so neat after all - refactor to regular methods checking for the method instead

class TorrentViewBase(Resource):
    """
    POST and PUT creates/updates a torrent
    """

    @login_required
    def post(self, req):
        form = UploadForm(req.POST, req.FILES)    
        if form.is_valid():
            t = _store_torrent(req, form)
            if not t:
                return HttpResponse('error creating torrent')
            _prefetch_existlink(t.hashval)
            return HttpResponseRedirect('/torrent/#%d' % t.id)
        else:
            return render_to_response('share/upload-torrent.html',
                                      make_response_dict(req,{'form': form}))
        
    @login_required
    def put(self, req):
        form = UploadForm(req.POST, req.FILES)
        if form.is_valid():
            t = _store_torrent(req, form)
            if not t:
                return HttpResponse('error creating torrent')
            _prefetch_existlink(t.hashval)
            return HttpResponseRedirect('/torrent/#%d' % t.id)
        else:
            logger.info("upload_form: received invalid form")

class TorrentForm(TorrentViewBase):

    @login_required
    def get(self, req):
        return render_to_response('share/upload-torrent.html',
                                   make_response_dict(req,{'form': UploadForm()}))

class TorrentView(TorrentViewBase):

    @login_required
    def get(self, request, inst=None):
        if not inst:
            return _torrentlist(request, find_torrents(request.user, request.GET.lists()))
        
        t = get_object_or_404(Torrent,pk=inst)
        d = torrentdict(request, t)
        return respond_to(request,
                          {'text/html': 'share/torrent.html',
                           'application/x-bittorrent': _torrent_file_response},d)

@login_required
def torrent_by_hashval(request, inst):
    try:
        t = Torrent.objects.get(hashval=inst)
    except ObjectDoesNotExist:
        return render_to_response('share/index.html',
                                  make_response_dict(request, {'error': "No such torrent: %s" % inst}))
    except MultipleObjectsReturned:
        return _torrentlist(request,
                            Torrent.objects.filter(hashval=inst).order_by('-creation_date'))
    return respond_to(request,
                      {'text/html': 'share/torrent.html',
                       'application/x-bittorrent': _torrent_file_response},
                      {'torrent': t})

@login_required
def search(request):
    term = None
    if request.REQUEST.has_key('q'):
        term = request.REQUEST['q']
    elif request.REQUEST.has_key('term'):
        term = request.REQUEST['term']
    
    if term:
        tag = find_torrents(request.user, [('tag',[term])])
        txt = find_torrents(request.user, [('txt',[term])])
        torrents = tag;
        torrents.extend(txt);
        return _torrentlist(request, torrents);
    else:
        return HttpResponseRedirect("/torrent")
