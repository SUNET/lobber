'''
Created on Aug 9, 2010

@author: leifj
'''

from django import template
 
register = template.Library()

def metainfofile(f):
    return "%s (%d bytes)" % ("/".join(f['path']),f['length'])

metainfofile.is_safe = True
register.filter(metainfofile)