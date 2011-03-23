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
import lobber.log
from lobber.share.forms import UploadForm, AddACEForm
from lobber.share.models import Torrent
from lobber.notify import notifyJSON
from lobber.share.forms import formdict
from tempfile import NamedTemporaryFile
import tempfile
from lobber.tracker.views import peer_status
from django.utils.datastructures import MultiValueDictKeyError
from lobber.userprofile.models import user_profile
from django.utils.html import escape

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

####################
# Helper functions.

from lobber.torrenttools import bdecode, bencode, make_meta_file
from hashlib import sha1

def _torrent_info(data):
    """
    Return (name, hash) of torrent file or None if an invalid file.
    """
    try:
        info = bdecode(data)['info']
    except Exception: # not a valid bencoded string
        return None, None
        
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
    
    # Read the files first 11 bytes
    first_bytes = ff.read(11)
    # Reset the file
    ff.seek(0, 0)
    
    if first_bytes.startswith('d8:announce'): 
        torrent_file_content = ''
        # FIXME: Limit amount read and check length of returned data.
        for chunk in ff.chunks():
            torrent_file_content += chunk
        ff.close()
    else:
        tmptf = NamedTemporaryFile(delete=False)
        datafile = file("%s%s%s" % (tempfile.gettempdir(),
                                    os.sep,
                                    _sanitize_fn(ff.name)),
                                    "w")
        for chunk in ff.chunks():
            datafile.write(chunk)
        datafile.close()
        make_meta_file(datafile.name,ANNOUNCE_URL, 2**18, comment=form.cleaned_data['description'], target=tmptf.name)
        torrent_file_content = tmptf.read()
        tmptf.close()
        ff.close()
        os.unlink(tmptf.name)
    
    torrent_name, torrent_hash = _torrent_info(torrent_file_content)
    if not torrent_name and not torrent_hash:
        logger.error('%s: Not a valid torrent file.' % ff.name)
        return None

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

def _find_torrents(user, args, max=40):
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

def _torrentdict(request,t,forms=None):
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

# Torrents

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
        return _torrentlist(request, _find_torrents(request.user, request.GET.lists()))
    
    t = get_object_or_404(Torrent,pk=inst)
    if not t.authz(request.user,'r'):
        return HttpResponseForbidden("You don't have read access on %s" % inst)
    
    d = _torrentdict(request, t)
    d['edit'] = True
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
        tag = _find_torrents(request.user, [('tag',[term])])
        txt = _find_torrents(request.user, [('txt',[term])])
        torrents = tag;
        torrents.extend(txt);
        return _torrentlist(request, torrents);
    else:
        return HttpResponseRedirect("/torrent")
    
    
## Tagging

@login_required
def tag_usage(request):
        r = None
        try:
            tags = []
            if request.GET.has_key('search'): 
                tags = filter(lambda x: x.name.startswith(request.GET['search']),Tag.objects.usage_for_model(Torrent,counts=False))
            else:
                tags = Tag.objects.usage_for_model(Torrent,counts=True)

            tagnames = [tag.name for tag in tags]
            profile = user_profile(request.user)
            tagnames.extend(profile.get_entitlements())
            r = json_response(tagnames)
        except MultiValueDictKeyError,e:
            logger.error(e)
        return r
    
@login_required
def tags(request,tid):
        t = get_object_or_404(Torrent,pk=tid)
        
        if request.method == 'POST':
            to_tags = request.POST.getlist('tags[]')
            from_tags = [tag.name for tag in Tag.objects.get_for_object(t)]
            Tag.objects.update_tags(t,' '.join(to_tags))
            
            # figure out the diff and notify subscribers
            for tag in from_tags:
                if not tag in to_tags:
                    notifyJSON("/torrent/tag/remove",tag)
            for tag in to_tags:
                if not tag in from_tags:
                    notifyJSON("/torrent/tag/add",tag)
        
        d = _torrentdict(request,t,formdict())
        d['edit'] = True
        return respond_to(request, {'application/json': json_response(d.get('tags')),
                                    'text/html': "share/torrent.html" },d)
    
@login_required
def list_torrents_for_tag(request,name):
        return respond_to(request,
                          {'text/html': 'share/index.html',
                           'application/rss+xml': 'share/rss2.xml',
                           'text/rss': 'share/rss2.xml'},
                          {'torrents': _find_torrents(request.user, [('tag',[name])]),
                           'title': 'Torrents tagged with '+name,
                           'tag': name,
                           'description': 'Torrents tagged with '+name})


## ACL

def valid_ace_p(ace):
    """Return True if ACE is a valid access control entry, otherwise
    False.

    BUG: We don't allow '.' and potential other characters needed.
    """
    entl, _, perm = ace.partition('#')
    if not entl or not perm:
        return False
    if not entl.replace(':', '').replace('_', '').isalnum():
        return False
    if len(perm) > 1:
        return False
    if not perm in 'rwd':
        return False
    return True        

@login_required
def add_ace(req, tid, ace):
    "Add ACE to ACL of torrent with id TID."
    t = get_object_or_404(Torrent,pk=int(tid))

    if not valid_ace_p(ace):
        return HttpResponse("invalid ace: %s" % escape(ace), status=400)

    if not t.add_ace(req.user, ace):
        return HttpResponse("Permission denied.", status=403)

    t.save()
    return respond_to(req,{'text/html': HttpResponseRedirect("/torrent/%d" % (t.id)),
                           'application/json': json_response(ace)})

@login_required
def remove_ace(req, tid, ace):
    "Remove ACE from ACL of torrent with id TID."
    t = get_object_or_404(Torrent,pk=int(tid))

    if not t.remove_ace(req.user, ace):
        return HttpResponse("Permission denied.", status=403)
        
    t.save()
    return respond_to(req,{'text/html': HttpResponseRedirect("/torrent/%d" % (t.id)),
                           'application/json': json_response(ace)})

@login_required
def edit(request,tid):
    t = get_object_or_404(Torrent,pk=int(tid))
    
    forms = formdict()
    if request.method == 'POST':
        form = forms['permissions'] = AddACEForm(request.POST)
        if form.is_valid():
            ace = "%s#%s" % (form.cleaned_data['entitlement'],''.join(form.cleaned_data['permissions']))
            t.add_ace(request.user,ace)
            t.save()
    
    d = _torrentdict(request,t,forms)
    d['edit'] = True
    return respond_to(request,{'text/html': 'share/torrent.html'},d)

