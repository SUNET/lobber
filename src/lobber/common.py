'''
Created on Dec 3, 2010

@author: leifj
'''

from django.http import HttpResponse

class HttpResponseNotAuthorized(HttpResponse):
    
    def __init__(self, content=None):
        self.status_code = 401
        HttpResponse.__init__(self)
        self['WWW-Authenticate'] = 'Key'
        self.content = content
        

'''
Can be replaced with .encode('hex')?
'''
def hexify(s):
    r = ''
    for n in range(0, len(s)):
        r += '%02x' % ord(s[n])
    return r
