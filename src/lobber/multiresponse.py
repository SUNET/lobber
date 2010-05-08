import mimeparse
import re
from django.conf import settings
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from lobber.settings import STOMP_HOST, STOMP_PORT, ORBITED_PREFIX, ANNOUNCE_URL, DEBUG
from lobber.share.models import UserProfile
from datetime import datetime

default_suffix_mapping = {"\.htm(l?)$": "text/html",
                          "\.json$": "application/json",
                          "\.rss$": "application/rss+xml",
                          "\.torrent$": "application/x-bittorrent"}

def _accept_types(request, suffix):
    for r in suffix.keys():
        p = re.compile(r)
        if p.search(request.path):
            return suffix.get(r)
    return None


def timeAsrfc822 ( theTime ) :
    import rfc822
    return rfc822 . formatdate ( rfc822 . mktime_tz ( rfc822 . parsedate_tz ( theTime . strftime ( "%a, %d %b %Y %H:%M:%S" ) ) ) )

def make_response_dict(request,d={}):
 
    if request.user.is_authenticated():
        d['user'] = request.user
        profile = None
        try:
            profile = request.user.profile.get();
        except ObjectDoesNotExist:
            profile = UserProfile()
            d['profile'] = profile

    d['stomp_host'] = STOMP_HOST
    d['stomp_port'] = STOMP_PORT
    d['orbited_prefix'] = ORBITED_PREFIX
    d['announce_url'] = ANNOUNCE_URL
    d['date'] = timeAsrfc822(datetime.now())
    if DEBUG is not None:
        d['debug'] = True

    return d
    
def respond_to(request, template_mapping, dict, suffix_mapping=default_suffix_mapping):
    accept = _accept_types(request, suffix_mapping)
    if accept is None:
        accept = (request.META['HTTP_ACCEPT'].split(','))[0]
    content_type = mimeparse.best_match(template_mapping.keys(), accept)
    template = None
    if template_mapping.has_key(content_type):
        template = template_mapping[content_type]
    else:
        template = template_mapping["text/html"]
    if callable(template):
        response = template(make_response_dict(request,dict))
    else:
        response = render_to_response(template,make_response_dict(request,dict))
        response['Content-Type'] = "%s; charset=%s" % (content_type, settings.DEFAULT_CHARSET)
    return response
