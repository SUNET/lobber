'''
Created on Aug 9, 2010

@author: leifj
'''

from django import template
from django.contrib.auth.models import User
from lobber.share.models import user_profile
from lobber.extensions.templatetags.userdisplay import userdisplay
 
register = template.Library()

def explainace(a):
    (ent,hash,perm) = a.rpartition("#")
    explain = {"r": "read","w": "read and write", "d": "remove"}
    what = " and ".join(explain[p] for p in perm)
    who = ""
    if not ent:
        who = "anyone"
    elif ent.startswith("user:"):
        (user,colon,theuser) = ent.partition(":")
        who = userdisplay(User.objects.get(username=theuser))
    elif ent == 'urn:x-lobber:storagenode':
        who = "all system storage nodes"
    else:
        who = ent
        
    return "%s can %s" % (who,what)

explainace.is_safe = True
register.filter(explainace)