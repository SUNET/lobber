'''
Created on Aug 9, 2010

@author: leifj
'''

from django import template
from django.contrib.auth.models import User
from lobber.extensions.templatetags.userdisplay import userdisplay
 
register = template.Library()

def explainace(a):
    explain = {"r": "read","w": "read and write", "d": "remove"}
    who = ""
    if not a.group and not a.user:
        who = "Anyone"
    elif a.user:
        who = userdisplay(a.user)
    else:
        who = "The group called '%s'" % a.group
        
    return "%s can %s" % (who,explain[a.permission])

explainace.is_safe = True
register.filter(explainace)