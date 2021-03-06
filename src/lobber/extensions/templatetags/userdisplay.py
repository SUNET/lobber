'''
Created on Oct 7, 2010

@author: leifj
'''

from django import template
from lobber.share.models import user_profile
 
register = template.Library()

def profiledisplay(profile):
    display = profile.display_name
    if not display:
        r = None
        if profile.user.username.startswith("key:") and profile.creator:
            display = "a key created by %s" % userdisplay(profile.creator)
        else:
            try:
                display, r = profile.user.username.split('@')
            except ValueError:
                display = profile.user.username
            if r:
                display = '%s (at %s)' % (display, r)
    if not display:
        display = "unknown user"
    return display


def userdisplay(u):
    profile = user_profile(u)
    display = profile.display_name
    if not display:
        r = None
        if u.username.startswith("key:") and profile.creator:
            display = "a key created by %s" % userdisplay(profile.creator)
        else:
            try:
                display, r = u.username.split('@')
            except ValueError:
                display = u.username
            if r:
                display = '%s (at %s)' % (display, r)
    if not display:
        display = "unknown user"
    return display

userdisplay.is_safe = True
register.filter(userdisplay)

profiledisplay.is_safe = True
register.filter(profiledisplay)