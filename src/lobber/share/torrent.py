import os
from datetime import datetime as dt

from django.http import HttpResponse, HttpResponseRedirect,\
    HttpResponseForbidden, HttpResponseServerError, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User

from tagging.models import Tag, TaggedItem

from lobber.multiresponse import respond_to, make_response_dict, json_response
from lobber.settings import TORRENTS, ANNOUNCE_URL, NORDUSHARE_URL, BASE_UI_URL, LOBBER_LOG_FILE, DROPBOX_DIR
from lobber.resource import Resource
import lobber.log
from lobber.share.forms import UploadForm
from lobber.share.models import Torrent, user_profile
from lobber.notify import notifyJSON
from lobber.share.forms import formdict
from tempfile import NamedTemporaryFile
from lobber.share.models import DataLocation
import tempfile
from lobber.tracker.views import peer_status

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

####################
# Helper functions. FIXME: Move to some other file.
from lobber.torrenttools import bdecode, bencode, make_meta_file
from hashlib import sha1

def _torrent_info(data):
    """
    Return (name, hash) of torrent file.
    """
    info = bdecode(data)['info']
    return info['name'], sha1(bencode(info)).hexdigest()

def _create_torrent(filename, announce_url, target_file, comment=None):
    make_meta_file(filename, announce_url, 2 ** 18, comment=comment, target=target_file)

def _sanitize_fn(name):
    import unicodedata, re
    # Normalize.
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore')
    # Remove everything but alphanumerics, underscore, space, period and dash.
    name = unicode(re.sub('[^\w\s.-]', '', name).strip())
    # Replace dashes and spaces with a single dash.
    name = unicode(re.sub('[-\s]+', '-', name))
    # Remove double periods.
    name = unicode(re.sub('\.\.', '', name))
    return name
    
def _sanitize_re(str):
    """
    When doing searches that starts with *, ?, +, ie. special regexp chars, 
    MySQLdb and psycopg2 will throw "OperationalError: (1139, "Got error 
    'repetition-operator operand invalid' from regexp")".
    This function returns a regexp string with the starting special chars 
    escaped.
    """
    special_chars = ['*','+','?']
    if str[0] in special_chars:
        return '\\%s' % str
    return str

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
    ff = form.cleaned_data['file']
    datafile = None
    if ff.content_type == 'application/x-bittorrent':
        # FIXME: Limit amount read and check length of returned data.
        torrent_file_content = ff.read()
        ff.close()
    else:
        tmptf = NamedTemporaryFile(delete=False)
        datafile = file("%s%s%s" % (tempfile.gettempdir(),
                                    os.sep,
                                    _sanitize_fn(ff.name)),
                        "w")
        datafile.write(ff.read())
        datafile.close()
        make_meta_file(datafile.name,ANNOUNCE_URL, 2**18, comment=form.cleaned_data['description'], target=tmptf.name)
        torrent_file_content = tmptf.read()
        tmptf.close()
        ff.close()
        os.unlink(tmptf.name)
    
    torrent_name, torrent_hash = _torrent_info(torrent_file_content)

    acl = []
    publicAccess = form.cleaned_data['publicAccess']
    if publicAccess:
        acl.append("#r")
    acl.append('user:%s#w' % req.user.username)
    acl.append('urn:x-lobber:storagenode#r')

    t = Torrent(acl=" ".join(acl),
                creator=req.user,
                name=torrent_name,
                description=form.cleaned_data['description'],
                expiration_date=form.cleaned_data['expires'],
                data='%s.torrent' % torrent_hash, # will change soon...
                hashval=torrent_hash)
    t.save()
    
    name_on_disk = '%s/%d.torrent' % (TORRENTS,t.id)
    f = file(name_on_disk, 'w')
    try:
        f.write(torrent_file_content)
        f.close()
        t.data = '%d.torrent' % t.id
        t.save()
    except Exception,ex:
        t.delete()
        logger.error(repr(ex))
        return None
    
    notifyJSON('/torrents/notify', {'add': [t.id,torrent_hash]})
    if datafile:
        os.rename(datafile.name,"%s%s%s" % (DROPBOX_DIR,os.sep,torrent_name)) # must be same FS - performance would suck otherwize
    return t
    
def _urlesc(s):
    r = ''
    for n in range(0, len(s), 2):
        r += '%%%s' % s[n:n+2].upper()
    return r

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
                re = _sanitize_re(re)
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
                       'application/json': json_response([{'label': t.name,'link': "/torrent/%d" % (t.id), 'id': t.id, 'info_hash': t.hashval} for t in torrents])},
                      {'torrents': torrents,
                       'refresh': 20, 
                       'title': 'Search result',
                       'description': 'Search result'})

def torrentdict(request,t,forms=None):
    if not forms:
        forms = formdict()
    tags = map(lambda t: t.name,t.readable_tags(request.user))
    acl = t.get_acl(request.user)
    lkey = ""
    if request.GET.has_key('lkey'):
        lkey = "?lkey=%s" % request.GET['lkey']
    return {'torrent': t,
            'lkey': lkey,
            'forms': forms,
            'tags': tags,
            'acl': acl,
            'read': t.authz(request.user,'r'), 
            'write': t.authz(request.user,'w'), 
            'delete': t.authz(request.user,'d')}

####################
# External functions, called from urls.py.

@login_required
def ihaz(request,hash,url=None):
    if url == None:
        url = "torrent:%s" % hash
        
    if Torrent.objects.filter(hashval=hash).count() > 0:
        DataLocation.objects.get_or_create(owner=request.user,url=url,hashval=hash)
        return json_response(url)
    else:
        return json_response("")
        
@login_required
def inohaz(request,hash,url=None):
    if url == None:
        url = "torrent:%s" % hash
    for loc in DataLocation.objects.filter(owner=request.user,url=url,hashval=hash).all():
        loc.delete()
    return json_response(url)
    
def _locations(hash,entitlement,scheme):
    locations = DataLocation.objects.filter(url__startswith=scheme,hashval=hash)
    #if entitlement != None:
    #    locations = locations.filter(owner__profile__entitlements__contains=entitlement)
        
    return locations.all()
    
def hazcount(request,hash,entitlement=None,scheme="torrent"):
    count = 0
    for dl in _locations(hash,entitlement,scheme):
        if entitlement != None:
            owner_profile = user_profile(dl.owner)
            if entitlement in owner_profile.get_entitlements():
                count = count+1
        else:
            count = count+1
    return json_response({'count': count})
    
def canhaz(request,hash,entitlement=None,scheme="http"):
    urls = []
    for dl in _locations(hash,entitlement,scheme):
        if entitlement != None:
            owner_profile = user_profile(dl.owner)
            if entitlement in owner_profile.get_entitlements():
                urls.append(dl.url)
        else:
            urls.append(dl.url)
    
    return json_response(urls)
    
def welcome(req):
    return HttpResponseRedirect("/torrent/")

@login_required
def remove_torrent(request, tid):
    t = get_object_or_404(Torrent,pk=tid)
    
    if not t.authz(request.user,'d') and not t.authz(request.user,'w'):
        return HttpResponseForbidden("Your are not allowed to remove this torrent")
    
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
        return HttpResponseNotFound("No such torrent")

    hash = t.hashval
    status = peer_status([hash])
    return json_response(status[hash])

@login_required
def scrape_hash(request,hash):
    qst = Torrent.objects.filter(hashval=hash);
    if not qst:
        return HttpResponseNotFound("No such torrent")
    t = qst[0]

    hash = t.hashval
    status = peer_status([hash])
    return json_response(status[hash])

@login_required
def upload_jnlp(req):
    d = {'sessionid': req.session.session_key,
         'announce_url': ANNOUNCE_URL,
         'baseurl': BASE_UI_URL,
         'apiurl': NORDUSHARE_URL} # ==> upload_form() via urls.py.
    return render_to_response('share/launch.jnlp', d,
                              mimetype='application/x-java-jnlp-file')

def exists_new(req,inst):
    count = Torrent.objects.filter(hashval=inst).count()
    r = None
    if count > 0:
        r = HttpResponse(inst)
        r['Cache-Control'] = 'max-age=604800'
    else:
        r = HttpResponseNotFound()
        r['Cache-Control'] = 'max-age=2'
    return r

def exists(req, inst):
    r = HttpResponse(status=200);
    r['Cache-Control'] = 'max-age=604800' # 1 week in seconds
    try:
        t = Torrent.objects.get(hashval=inst)
        r.content = t.hashval
    except ObjectDoesNotExist:
        r.status_code = 404
        r['Cache-Control'] = 'max-age=2'
    except MultipleObjectsReturned:
        pass                            # Ok.
    return r;

def add_torrent(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)        
        if form.is_valid():
            t = _store_torrent(request, form)
            if not t:
                return HttpResponseServerError('error creating torrent')
            return respond_to(request,
                              {'application/json': json_response(t.id),
                               'text/html': HttpResponseRedirect("/torrent#%d" % t.id)})
    else:
        form = UploadForm()
        
    return respond_to(request,
                      {'application/json': HttpResponseServerError("Invalid request"),
                       'text/html': 'share/upload-torrent.html'},{'form': form})


@login_required
def show(request, inst=None):
    if not inst:
        return _torrentlist(request, find_torrents(request.user, request.GET.lists()))
    
    t = get_object_or_404(Torrent,pk=inst)
    if not t.authz(request.user,'r'):
        return HttpResponseForbidden("You don't have read access on %s" % inst)
    
    d = torrentdict(request, t)
    d['edit'] = True
    return respond_to(request,
                      {'text/html': 'share/torrent.html',
                       'application/x-bittorrent': _torrent_file_response},d)

@login_required
def land(request, inst):
    t = get_object_or_404(Torrent,pk=inst)
    if not t.authz(request.user,'r'):
        return HttpResponseForbidden("You don't have read access on %s" % inst)
    
    d = torrentdict(request, t)
    d['edit'] = False
    return respond_to(request,
                      {'text/html': 'share/torrent.html',
                       'application/x-bittorrent': _torrent_file_response},d)

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
        if not t.authz(request.user,'r'):
            return HttpResponseForbidden("You don't have read access on %s" % inst)
        
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
                                  make_response_dict(request, {'refresh': 20,'error': "No such torrent: %s" % inst}))
    except MultipleObjectsReturned:
        return _torrentlist(request,
                            filter(lambda t: t.authz(request.user,'r'),Torrent.objects.filter(hashval=inst).order_by('-creation_date')))
        
    if not t.authz(request.user,'r'):
        return HttpResponseForbidden("You don't have read access on %s" % inst)
    
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
