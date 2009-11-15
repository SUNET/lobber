from datetime import datetime as dt
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from forms import UploadTorrentForm
from lobber.share.models import Torrent, Handle

def torrent_list(req):
    MAX = 20
    handles = Handle.objects.all().order_by('-creation')[:MAX]
    torrents = []
    for h in handles:
        if h.published and h.expiration > dt.now():
            if not h.torrent in torrents:
                torrents.append(h.torrent)
    return render_to_response('share/index.html', {'torrents': torrents})

from BitTorrent.bencode import bdecode, bencode
from hashlib import sha1
def do_hash(data):                      # FIXME: Move.
    cont = bdecode(data)
    info = cont['info']
    return sha1(bencode(info)).hexdigest()

# from django.core.files.uploadedfile import SimpleUploadedFile
def torrent_add(req):
    #return HttpResponse('ok')
    if req.method == 'POST':
        form = UploadTorrentForm(req.POST, req.FILES)
        if form.is_valid():
            # TODO: Process form.cleaned_data (a dict keyed with form
            # members).
            tfile = req.FILES['file']
            t = Torrent(#owner = current user,
                        name = form.cleaned_data['name'],
                        data = tfile.name,
                        hashval = do_hash(tfile.read()))
            t.save()
            h = Handle(torrent = t,
                       name = form.cleaned_data['name'],
                       published = form.cleaned_data['published'],
                       #creation = ,
                       expiration = form.cleaned_data['expires'])
            h.save()
            return HttpResponseRedirect('../%s/' % h.id)
    else:
        form = UploadTorrentForm()
    return render_to_response('share/upload.html', {'form': form})

def torrent_view(req, handle_id):
    h = Handle.objects.get(id__exact = int(handle_id))
    return render_to_response('share/torrent.html', {'torrent': h.torrent})
