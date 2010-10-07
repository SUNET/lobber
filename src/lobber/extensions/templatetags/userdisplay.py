'''
Created on Oct 7, 2010

@author: leifj
'''

from django import template
from lobber.share.models import user_profile
 
register = template.Library()

def userdisplay(u):
    return user_profile(u).display_name

userdisplay.is_safe = True
register.filter(userdisplay)