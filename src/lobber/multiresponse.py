from lobber import mimeparse
import re
from django.conf import settings
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from lobber.settings import STOMP_HOST, STOMP_PORT, ORBITED_PREFIX, ANNOUNCE_URL, DEBUG
from lobber.userprofile.models import UserProfile
from datetime import datetime
from django.http import HttpResponse
from orbited import json
from lobber.share.models import Torrent
from tagging.models import TaggedItem, Tag
from tagging.utils import calculate_cloud

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

def make_response_dict(request,d_in={}):

    d = d_in
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
    d['tagcloud'] = make_tag_cloud(request)
    if DEBUG is not None:
        d['debug'] = True

    return d


def _adjust_count_to_readable(tag,user):
    tag.count = len(filter(lambda t: t.authz(user,'r'),TaggedItem.objects.get_by_model(Torrent, tag).all()))
    return tag

def make_tag_cloud(request):
    if request.user.is_authenticated():
        return calculate_cloud(filter(lambda x: x.count > 0,[_adjust_count_to_readable(tag,request.user) for tag in Tag.objects.usage_for_model(Torrent, counts=True)]))
    else:
        return []

def json_response(data): 
    r = HttpResponse(json.encode(data),content_type='application/json')
    r['Cache-Control'] = 'no-cache, must-revalidate'
    r['Pragma'] = 'no-cache'
    
    return r
    
def respond_to(request, template_mapping, dict={}, suffix_mapping=default_suffix_mapping):
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
    elif isinstance(template, HttpResponse):
        response = template
        response['Content-Type'] = "%s; charset=%s" % (content_type, settings.DEFAULT_CHARSET)
    else:
        response = render_to_response(template,make_response_dict(request,dict))
        response['Content-Type'] = "%s; charset=%s" % (content_type, settings.DEFAULT_CHARSET)
    return response
