'''
Created on Dec 3, 2010

@author: leifj
'''

from django.http import HttpResponse

class HttpResponseNotAuthorized(HttpResponse):
    
    def __init__(self, content=None):
        self.status_code = 401
        HttpResponse.__init__(self)
        self['WWW-Authenticate'] = 'Key' # Better with something than nothing?
        self.content = content
