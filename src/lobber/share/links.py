import os
import StringIO
import exceptions
from datetime import datetime as dt
from hashlib import sha256
from random import getrandbits

from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotModified
from django.shortcuts import render_to_response
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from twisted.internet import defer
from time import gmtime, strftime, sleep

from lobber.settings import BASE_DIR, LOGIN_URL, ANNOUNCE_URL, NORDUSHARE_URL, BASE_UI_URL, LOBBER_LOG_FILE
from lobber.share.models import Torrent, Tag, UserProfile
from lobber.notify.mail import sendmail
from forms import UploadForm, CreateKeyForm

from lobber.resource import Resource
import lobber.log
logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

def _create_key_user(creator, urlfilter, entitlements, expires=None):
    # FIXME: Do random.seed() somewhere.
    # FIXME: Is 256 bits of random data proper?
    # FIXME: Don't chop the digest!!!  Necessary for now, since
    # Djangos User class allows for max 30 characters user names.
    secret = sha256(str(getrandbits(256))).hexdigest()[:26]
    username = 'key:%s' % secret
    user = User.objects.create_user(username, 'nomail@dev.null', username)

    lst = map(lambda s: s.replace('$self', username), entitlements.split())
    entls = ' '.join(map(lambda e: 'user:%s:%s' % (creator.username, e), lst))
    profile = UserProfile(user=user,
                          creator=creator,
                          urlfilter=' '.join(urlfilter.split()),
                          entitlements=entls,
                          expiration_date=expires)
    profile.save()
    return secret
    
def _make_share_link(req,tid):
    try:
        t = Torrent.objects.get(id=int(tid))
    except ObjectDoesNotExist:
        return HttpResponse('Sorry, torrent %s not found'  % tid)
    key = _create_key_user(creator=req.user,
                           urlfilter='torrent/%s' % tid, # FIXME: Append '$'?
                           entitlements='user:%s:$self' % req.user.username)
    t.add_ace('user:%s:%s#r' % (req.user.username, key))
    #link = '%s/%s?lkey=%s' % (NORDUSHARE_URL, tid, key)
    return '%s/torrent/%s.torrent?lkey=%s' % (NORDUSHARE_URL, t.hashval, key)

@login_required
def gimme_url_for_reading_torrent(req, tid):
    link = _make_share_link(req,tid)
    return HttpResponse('<a href=\"%s\">%s</a>' % (link, link))

def addToList(d,session,tag,msg):
   if not session.has_key(tag):
      session[tag] = []
   session[tag].append(msg)

@login_required
def get_notices(req,tag):
   while True:
      if req.session.has_key(tag):
         l = req.session[tag]
         req.session[tag] = []
         return HttpResponse("\n".join(l))
      time.sleep(2000)

@login_required
def send_link_mail(req,tid):
    to = req.REQUEST.get('to')
    message = req.REQUEST.get('message')
    link = _make_share_link(req,tid)
    f = StringIO.StringIO()
    f.write("Data: "+strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))
    f.write("From: "+req.user.email)
    f.write("To: "+to)
    f.write("Subject: "+req.user.get_full_name()+" has shared some data with you")
    f.write("\n")
    f.write("Follow this link to download the data using a torrent client: "+link)
    d = sendmail(req.user.email,[to],f)
    d.addCallback(addToList,req.session,'info',"Message to "+to+" sent")
    d.addErrback(addToList,req.session,'error',"There was a problem sending mail to "+to)
    return HttpResponse()
