from django.http import HttpResponse

def torrent_list(req):
    return HttpResponse("list of torrents")

def torrent_view(req, handle):
    return HttpResponse("torrent with handle '%s'" % handle)

