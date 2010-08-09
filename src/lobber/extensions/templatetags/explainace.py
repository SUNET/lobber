'''
Created on Aug 9, 2010

@author: leifj
'''

from django import template
 
register = template.Library()

def explainace(a):
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

explainace.is_safe = True
register.filter(explainace)