from hashlib import sha256
from random import getrandbits
from pprint import pprint

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from time import gmtime, strftime
from orbited import json

from lobber.share.users import create_key_user
from lobber.settings import NORDUSHARE_URL, LOBBER_LOG_FILE
from lobber.share.models import Torrent, UserProfile
from lobber.notify import notify
import lobber.log
logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

def _make_share_link(req, tid):
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return None
    key = create_key_user(creator=req.user,
                          urlfilter='torrent/%s' % tid, # FIXME: Append '$', limiting more?
                          entitlements='user:%s:$self' % req.user.username)
    t.add_ace('user:%s:%s#r' % (req.user.username, key))
    return '%s/torrent/%s.torrent?lkey=%s' % (NORDUSHARE_URL, t.hashval, key)

@login_required
def gimme_url_for_reading_torrent(req, tid):
    link = _make_share_link(req,tid)
    if link is None:
        return HttpResponse('Sorry, torrent %s not found'  % tid)
    return HttpResponse('<a href=\"%s\">%s</a>' % (link, link))

@login_required
def send_link_mail(req,tid):
    to = req.REQUEST.get('to')
    message = req.REQUEST.get('message')
    link = _make_share_link(req,tid)
    if link is None:
        return HttpResponse('Sorry, torrent %s not found'  % tid)
    msg = "Data: "+strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())+"\n"
    msg += "From: "+req.user.email+"\n"
    msg += "To: "+to+"\n"
    msg += "Subject: "+req.user.get_full_name()+" has shared some data with you\n"
    msg += "\n"
    msg += "Follow this link to download the data using a torrent client: "+link+"\n"
    msg += message
    msg += "\n"
    notify("/agents/sendmail",json.encode({'notify_to': "/session/%s" % req.session.session_key,
                                           'to': [to], 
                                           'sender': req.user.email,
                                           'message': msg}));
    return HttpResponse()
