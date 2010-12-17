from lobber.tracker.models import PeerInfo
from datetime import datetime, timedelta

def purge_old_tracker_peers():
    ti = datetime.now() - timedelta(minutes=1)
    q = PeerInfo.objects.filter(last_seen__lt=ti)
    for t in q:
        if t.state == PeerInfo.STOPPED:
            #print "DEBUG: removing peer %s" % t
            t.delete()

purge_old_tracker_peers()
