
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.html import escape

from lobber.share.models import Torrent
from django.core.exceptions import ObjectDoesNotExist
from lobber.multiresponse import respond_to
from lobber.share.forms import AddACEForm

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
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return HttpResponse("Torrent with id %d not found." % int(tid), status=404)

    if not valid_ace_p(ace):
        return HttpResponse("invalid ace: %s" % escape(ace), status=400)

    if not t.add_ace(req.user, ace):
        return HttpResponse("Permission denied.", status=403)

    t.save()
    return HttpResponseRedirect("/torrent/%d/ace" % (t.id))

@login_required
def remove_ace(req, tid, ace):
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return HttpResponse("Torrent with id %d not found." % int(tid), status=404)

    if not t.remove_ace(req.user, ace):
        return HttpResponse("Permission denied.", status=403)
        
    t.save()
    return HttpResponseRedirect("/torrent/%d/ace" % (t.id))

@login_required
def edit(req,tid):
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return HttpResponse("Torrent with id %d not found." % int(tid), status=404)
 
    if req.method == 'POST':
        form = AddACEForm(req.POST)
        if form.is_valid():
            ace = "%s#%s" % (form.cleaned_data['entitlement'],''.join(form.cleaned_data['permissions']))
            t.add_ace(req.user,ace)
            t.save()
    else:
        form = AddACEForm()
          
    return respond_to(req, 
                      {'text/html': 'share/acl.html'}, 
                      {'torrent': t, 'acl': t.get_acl(req.user), 'form': form})
