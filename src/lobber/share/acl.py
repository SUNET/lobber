
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.html import escape

from lobber.share.models import Torrent
from django.core.exceptions import ObjectDoesNotExist
from lobber.multiresponse import respond_to, json_response
from lobber.share.forms import AddACEForm
from django.shortcuts import get_object_or_404
from lobber.share.torrent import torrentdict
from lobber.share.forms import formdict

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
    
    d = torrentdict(request,t,forms)
    return respond_to(request,{'text/html': 'share/torrent.html'},d)
