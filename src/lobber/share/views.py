import os
from datetime import datetime as dt
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.servers.basehttp import FileWrapper
from forms import UploadTorrentForm
from lobber.share.models import Torrent, Handle
from settings import BASE_DIR, MEDIA_ROOT

def torrent_list(req):
    MAX = 40
    handles = Handle.objects.all().order_by('-creation')[:MAX]
    torrents = []
    for h in handles:
        if h.published and h.expiration > dt.now():
            if not h.torrent in torrents:
                torrents.append(h.torrent)
    return render_to_response('share/index.html', {'torrents': torrents})

####################
# FIXME: Move this to some other file.
from BitTorrent.bencode import bdecode, bencode
from hashlib import sha1
def do_hash(data):
    cont = bdecode(data)
    info = cont['info']
    return sha1(bencode(info)).hexdigest()

def add_hash_to_whitelist(thash):
    wlf = file('%s/%s' % (BASE_DIR, 'tracker-whitelist'), 'w+')
    wlf.write(thash + '\n')
    wlf.close()
    pidf = file('%s/%s' % (BASE_DIR, 'tracker.pid'), 'r')
    pid = int(pidf.read())
    pidf.close()
    os.kill(pid, 1)
    
####################

def torrent_add(req):
    if req.method == 'POST':
        form = UploadTorrentForm(req.POST, req.FILES)
        if form.is_valid():
            # Store torrent file in file system and add its hash to
            # the trackers whitelist.
            tfile = req.FILES['file']
            content = tfile.read()
            thash = do_hash(content)
            f = file('%s/torrents/%s' % (MEDIA_ROOT, tfile.name), 'w')
            f.write(content)
            f.close()
            t = Torrent(#owner = <current user>,
                        name = form.cleaned_data['name'],
                        data = tfile.name,
                        hashval = thash)
            t.save()
            h = Handle(torrent = t,
                       name = form.cleaned_data['name'],
                       published = form.cleaned_data['published'],
                       #creation = ,
                       expiration = form.cleaned_data['expires'])
            h.save()
            add_hash_to_whitelist(thash)
            return HttpResponseRedirect('../%s' % h.id)
    else:
        form = UploadTorrentForm()
    return render_to_response('share/upload.html', {'form': form})

def torrent_view(req, handle_id):
    h = Handle.objects.get(id__exact = int(handle_id))
    return render_to_response('share/torrent.html', {'torrent': h.torrent})

def torrent_get(req, tfile):
    fn = '%s/torrents/%s' % (MEDIA_ROOT, tfile)
    response = HttpResponse(FileWrapper(file(fn)), content_type='text/plain')
    response['Content-Length'] = os.path.getsize(fn)
    return response
