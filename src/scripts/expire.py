from lobber.share.models import Torrent
import datetime

def purge_old_torrents():
    q = Torrent.objects.filter(expiration_date__lt=datetime.datetime.now())
    for t in q:
        #print "DEBUG: removing %s" % t
        t.remove()

purge_old_torrents()
