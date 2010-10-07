from lobber.share.models import Torrent, UserProfile
import datetime

def purge_old_torrents():
    q = Torrent.objects.filter(expiration_date__lt=datetime.datetime.now())
    for t in q:
        #print "DEBUG: removing torrent %s" % t
        t.remove()
    return len(q)

def purge_old_key_users():
    q = UserProfile.objects.filter(expiration_date__lt=datetime.datetime.now())
    count = 0
    for p in q:
        u = p.user
        if u.username.startswith('key:'):
            #print "DEBUG: removing user profile %s and user %s" % (p, u)
            u.delete()
            p.delete()
            count += 1
    return count

purge_old_torrents()
purge_old_key_users()
