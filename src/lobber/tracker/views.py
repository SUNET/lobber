'''
Created on Oct 17, 2010

@author: leifj
'''
 
from lobber.tracker.models import PeerInfo
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from deluge.bencode import bencode
from socket import gethostname
from lobber.share.models import Torrent
from urllib import unquote
import struct
from ctypes import create_string_buffer

import lobber.log
from lobber.settings import LOBBER_LOG_FILE
logger = lobber.log.Logger("tracker", LOBBER_LOG_FILE)

def _hexify(s):
    r = ''
    for n in range(0, len(s)):
        r += '%02x' % ord(s[n])
    return r

def _err(msg):
    return HttpResponse(bencode({'failure reason': msg}),mimetype='text/plain')

def peer_address(request):
    port = None
    ip = None
    if request.GET.has_key('port'):
        port = request.GET['port']
        
    if request.GET.has_key('ipv6'):
        ipv6 = request.GET['ipv6']
        if ':' in ipv6:
            ip = ipv6
            
    if not ip and request.GET.has_key('ip'):
        ip = request.GET['ip']
    
    if not ip:
        ip = request.META['REMOTE_ADDR']
        
    return ip,port

def get_from_qs(qs, key):
    res = None
    i = qs.find(key)
    if i >= 0:
        i2 = qs[i:].find('&')
        if i2 >= 0:
            res = qs[i+len(key):i2]
    return res

def announce(request,info_hash=None):
    
    if not info_hash and request.GET.has_key('info_hash'):
        info_hash = get_from_qs(request.META['QUERY_STRING'], 'info_hash=')
        #logger.debug("announce: getting hash from request: %s" % request.META['QUERY_STRING'])
    
    if not info_hash:
        return _err('Missing info_hash')

    info_hash = _hexify(unquote(info_hash))
    #logger.debug("announce: info_hash=%s" % info_hash)


    #t = Torrent.objects.filter(hashval=info_hash)[:1]
    #if not t:
    #    return _err("Not authorized")
    
    pi = None
    #if request.GET.has_key('trackerid'):
    #    try:
    #        pi = PeerInfo.objects.get(pk=request.GET['trackerid'])
    #    except Exception,ex:
    #        pass
        
    ip,port = peer_address(request)
    
    if pi == None:
        pi,created = PeerInfo.objects.get_or_create(info_hash=info_hash,port=port,address=ip)
    
    if request.user and not request.user.is_anonymous:
        pi.user = request.user
        
    DEFNUMWANT = 50
    MAXNUMWANT = 200

    numwant = DEFNUMWANT
    if request.GET.has_key('numwant'):
        numwant = int(request.GET['numwant'])
        if numwant > MAXNUMWANT:
            numwant = MAXNUMWANT
        if numwant < 0:
            numwant = DEFNUMWANT

    for key in ('port','uploaded','downloaded','left','corrupt'):
        if request.GET.has_key(key):
            value = request.GET[key]
            key = key.replace(' ','_')
            setattr(pi,key,int(value))

    event = None
    if request.GET.has_key('event'):
        event = request.GET['event']
        
    if request.GET.has_key('peer_id'):
        pi.peer_id = request.GET['peer_id']
        
    compact = True
    if request.GET.has_key('compact') and not request.GET['compact']:
        compact = False
    
    if event == 'stopped':
        pi.state = PeerInfo.STOPPED
    elif event == 'completed':
        pi.state = PeerInfo.COMPLETED 
    elif event == 'paused':
        pi.state = PeerInfo.PAUSED  
    elif event == 'started':
        pi.state = PeerInfo.STARTED
    
    pi.save()
    p4str = create_string_buffer(numwant*6+1)
    p6str = create_string_buffer(numwant*18+1)
    offset = 0
    #dict = {'tracker id': "%d" % pi.id}
    dict = {}
    seeding = 0
    downloaded = 0
    count = 0
    
    if not compact:
        dict['peers'] = []
    
    for pi in PeerInfo.objects.filter(info_hash=info_hash)[:numwant]:
        if pi.state == PeerInfo.STARTED or pi.state == PeerInfo.COMPLETED:
            count = count + 1
            if pi.left == 0:
                seeding = seeding + 1
            
            if pi.state == PeerInfo.COMPLETED:
                downloaded = downloaded + 1
                      
            if compact:
                offset = offset + pi.pack_peer(p4str,p6str,offset)
            else:
                dict['peers'].append(pi.dict())
    
    dict['complete'] = seedingdiff --git a/src/lobber/tracker/views.py b/src/lobber/tracker/views.py
index e9b2566..32a6d97 100644
--- a/src/lobber/tracker/views.py
+++ b/src/lobber/tracker/views.py
@@ -158,9 +158,9 @@ def announce(request,info_hash=None):
     
     if compact:
         if p4str.value:
-            dict['peers'] = p4str.raw
+            dict['peers'] = p4str.raw[:offset]
         if p6str.value:
-            dict['peers6'] = p6str.raw
+            dict['peers6'] = p6str.raw[:offset]
             
     #logger.debug("announce: %s:%s (%s): compact=%s, offset=%d, dict=%s" % (ip, port, repr(info_hash), compact, offset, repr(dict)))
     return tracker_response(dict)

    dict['downloaded'] = downloaded
    dict['incomplete'] = count - seeding
    dict['interval'] = 10
    
    if compact:
        if p4str.value:
            dict['peers'] = p4str.raw[:offset]
        if p6str.value:
            dict['peers6'] = p6str.raw[:offset]
            
    #logger.debug("announce: %s:%s (%s): compact=%s, offset=%d, dict=%s" % (ip, port, repr(info_hash), compact, offset, repr(dict)))
    return tracker_response(dict)
    
def tracker_response(dict):
    return HttpResponse(bencode(dict),mimetype="text/plain")

def summarize(qs):
    count = 0
    downloaded = 0
    seeding = 0
    for pi in qs:
        if pi.state == PeerInfo.STARTED or pi.state == PeerInfo.COMPLETED:
            count = count + 1
            if pi.left == 0:
                seeding = seeding + 1
            
            if pi.state == PeerInfo.COMPLETED:
                downloaded = downloaded + 1
    return count,downloaded,seeding
    
def peer_status(hashvals):
    files = {}
    for info_hash in hashvals:
        count,downloaded,seeding = summarize(PeerInfo.objects.filter(info_hash=info_hash))
        files[info_hash]= {'complete': seeding, 'downloaded': downloaded, 'incomplete': count - seeding}
    return files;
    
def scrape(request):
    if request.GET.has_key('info_hash'):
        return tracker_response({'files': peer_status(request.GET.getlist('info_hash'))})
    else:
        return _err("I'm not going to tell you about all torrents n00b!")
    
@login_required
def user_announce(request):
    return announce(request)
