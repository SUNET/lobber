import re

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.html import escape

from lobber.share.models import Torrent
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from lobber.multiresponse import json_response, respond_to
from lobber.share.forms import ACLForm
from pprint import pprint

@login_required
def suggested_ace(req):
    profile = req.user.profile.get()
    entitlements = profile.get_entitlements()
    ace = map(lambda e: "%s#w" % e, entitlements)
    for e in map(lambda e: "%s#r" % e, entitlements): 
        ace.append(e)
    ace.append("#r")
    return json_response(map(lambda p: (p,_explain_ace(p)),ace))

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
    return HttpResponse("Access control entry %s set on torrent %s." % (ace, t))

@login_required
def remove_ace(req, tid, ace):
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return HttpResponse("Torrent with id %d not found." % int(tid), status=404)

    if not t.remove_ace(req.user, ace):
        return HttpResponse("Permission denied.", status=403)
        
    t.save()
    return HttpResponse("Access control entry %s removed from torrent %s." % (escape(ace), t))

def _explain_ace(a):
    (ent,hash,perm) = a.rpartition("#")
    p = {"r": "read","w": "read and write", "d": "remove"}
    what = p[perm]
    who = ""
    if not ent:
        who = "anyone"
    elif ent.startswith("user:"):
        (user,colon,theuser) = ent.partition(":")
        who = theuser
    elif ent == 'urn:x-lobber:storagenode':
        who = "all storage nodes"
    else:
        who = ent
        
    return "%s can %s" % (who,what)
    

@login_required
def edit(req,tid):
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return HttpResponse("Torrent with id %d not found." % int(tid), status=404)
    
    if req.method == 'GET':
        acl = t.get_acl(req.user)
        form = ACLForm(initial={'acl': acl})
        form.fields['acl'].choices = [(a,_explain_ace(a)) for a in acl]
        return respond_to(req, 
                          {'text/html': 'share/acl.html'}, 
                          {'torrent': t, 'acl': acl, 'form': form})
    elif req.method == 'POST':
        form = ACLForm(req.POST, req.FILES)
        if form.is_valid():
            acl = form.cleaned_data['acl']
            if not acl:
                acl = ()
            t.set_ace(req.user,acl)
            return HttpResponseRedirect("/torrent#"+t.id)
        else:
            return respond_to(req, 
                          {'text/html': 'share/acl.html'}, 
                          {'torrent': t, 'acl': t.get_acl(req.user), 'form': form})
