from time import gmtime, strftime

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from orbited import json

from lobber.share.users import create_key_user
from lobber.settings import NORDUSHARE_URL
from lobber.share.models import Torrent
from lobber.notify import notify
from django.shortcuts import get_object_or_404

def _make_share_link(user, torrent, expires=None):
    key = create_key_user(creator=user,
                          urlfilter='/torrent/%d.torrent[^/]*$' % torrent.id,
                          tagconstraints='',
                          entitlements='user:%s:$self' % user.username,
                          expires=expires)
    if not key:
        return None
    torrent.add_ace(user, 'user:%s:%s#r' % (user.username, key))
    return '%s/torrent/%d.torrent?lkey=%s' % (NORDUSHARE_URL, torrent.id, key)

@login_required
def gimme_url_for_reading_torrent(req, tid):
    t = get_object_or_404(Torrent,pk=tid);
    
    expiration = req.REQUEST.get('expiration');
    link = _make_share_link(req.user, t, expiration)
    if link is None:
        return HttpResponse('error: unable to create key user')
    return HttpResponse('<a href=\"%s\">%s</a>' % (link, link))

@login_required
def send_link_mail(req,tid):
    t = get_object_or_404(Torrent,pk=tid);
    
    expiration = req.REQUEST.get('expiration');
    to = req.REQUEST.get('to')
    message = req.REQUEST.get('message')
    link = _make_share_link(req.user, t, expiration)
    if link is None:
        return HttpResponse('error: unable to create key user')
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

@login_required
def gimme_url_for_reading_tag(request, tagstr):
    key = create_key_user(creator=request.user,
                          urlfilter='/torrent/tag/%s /torrent/.*[^/]+$' % tagstr,
                          tagconstraints=tagstr,
                          entitlements='user:%s:$self' % request.user.username)
    if not key:
        return HttpResponse('error: unable to create key user')
    link = '%s/torrent/tag/%s.rss?lkey=%s' % (NORDUSHARE_URL, tagstr, key)
    return HttpResponse('<a href=\"%s\">%s</a>' % (link, link))
