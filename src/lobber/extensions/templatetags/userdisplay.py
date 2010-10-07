'''
Created on Oct 7, 2010

@author: leifj
'''

from django import template
from lobber.share.models import user_profile
 
register = template.Library()

def userdisplay(u):
    display = user_profile(u).display_name
    if not display:
        r = None
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
