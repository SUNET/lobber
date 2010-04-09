import mimeparse
import re
import sys
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import Context
from django.template import RequestContext

default_suffix_mapping = { "\.htm(l?)$": "text/html", "\.json$": "application/json", "\.torrent$": "application/x-bittorrent"}

def _accept_types(request, suffix):
   for r in suffix.keys():
      p = re.compile(r)
      if p.search(request.path):
         return suffix.get(r)
   return None
    
def respond_to(request, template_mapping, dict, suffix_mapping=default_suffix_mapping):
   accept = _accept_types(request, suffix_mapping)
   if accept is None:
      accept = (request.META['HTTP_ACCEPT'].split(','))[0]
   content_type = mimeparse.best_match(template_mapping.keys(),accept)
   template = template_mapping[content_type]
   if callable(template):
      response = template(dict)
   else:
      response = render_to_response(template,dict)
      response['Content-Type'] = "%s; charset=%s" % (content_type, settings.DEFAULT_CHARSET)
   return response
