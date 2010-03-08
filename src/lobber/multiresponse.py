try:
    from functools import update_wrapper
except ImportError:
    from django.utils.functional import update_wrapper

import mimeparse
import re
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import Context
from django.template import RequestContext

default_suffix_mapping = { ".htm(l?)$": "text/html", ".json$": "application/json", ".torrent$": "application/x-bittorrent"}

class MultiResponse(object):
    def accept_types(self, request, suffix_mappping):
	for re in suffix_mappings.keys():
	    p = re.compile(re)
	    if p.match(request.path):
		return suffix_mappings.get(re)
        return None
    
    def __init__(self, template_mapping, suffix_mapping=default_suffix_mapping, request_context=True):
        self.template_mapping = template_mapping
        self.request_context = request_context

    def __call__(self, view_func):
        def wrapper(request, *args, **kwargs):
            context_dictionary = view_func(request, *args, **kwargs)
            context_instance = self.request_context and RequestContext(request) or Context()
            accept = self.accept_types(request, suffix_mapping)
            if accept is None:
	       accept = request.META['HTTP_ACCEPT']
            content_type = mimeparse.best_match(self.template_mapping.keys(),accept)
            response = render_to_response(self.template_mapping[content_type],
                                          context_dictionary,
                                          context_instance=context_instance)
            response['Content-Type'] = "%s; charset=%s" % (content_type, settings.DEFAULT_CHARSET)
            return response
        update_wrapper(wrapper, view_func)
        return wrapper

