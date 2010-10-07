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
        display = u.username
    if not display:
        display = "unknown user"
    return display

userdisplay.is_safe = True
register.filter(userdisplay)
