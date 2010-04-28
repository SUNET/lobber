import re
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from lobber.share.models import Torrent

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
    """Add ACE to ACL of torrent with id TID.
    Return torrent object if successful.
    """
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return HttpResponse("Torrent with id %d not found." % int(tid), status=404)
    fullace = t.add_ace(req.user, ace)
    if not fullace:
        return HttpResponse("%s: invalid ace: %s" % escape(ace))
    return HttpResponse("Access control entry %s set on torrent %s." % (fullace, t))

@login_required
def remove_ace(req, tid, ace):
    pass
