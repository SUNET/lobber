'''
Created on Oct 17, 2010

@author: leifj
'''
 
from lobber.tracker.models import PeerInfo
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from lobber.torrenttools import bencode
from lobber.share.models import Torrent, user_profile
from urllib import unquote
from ctypes import create_string_buffer
from binascii import hexlify, unhexlify

import lobber.log
from lobber.settings import LOBBER_LOG_FILE
from pprint import pformat
logger = lobber.log.Logger("tracker", LOBBER_LOG_FILE)

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
    for q in qs.split('&'):
        if q.startswith(key):
            return q[len(key):]
    
def announce(request,info_hash=None):
    
    logger.debug("announce called: %s" % pformat(request.META))
    
    if not info_hash and request.GET.has_key('info_hash'):
        info_hash = get_from_qs(request.META['QUERY_STRING'], 'info_hash=')
        #logger.debug("announce: getting hash from request: %s" % request.META['QUERY_STRING'])
    
    if not info_hash:
        return _err('Missing info_hash')

    info_hash = hexlify(unquote(info_hash))
    #logger.debug("announce: info_hash=%s" % info_hash)
    
    event = None
    if request.GET.has_key('event'):
        event = request.GET['event']
    
    torrents = Torrent.objects.filter(hashval=info_hash)
    try:
        logger.debug(torrents)
        if not (torrents or event == 'stopped' or event == 'paused'):
            #logger.debug("unauthorized")
            return _err("Not authorized")
    except Exception as e: # Database specific exception
        logger.error("Database unavailable: %s" % e)
        return _err('Database unavailable')
    
    ip,port = peer_address(request)
    #logger.debug("called from %s:%s" % (ip,port))
    pi = None
    qs = PeerInfo.objects.filter(info_hash=info_hash,port=port,address=ip)
    #logger.debug("qs1: %s" % pformat(qs))
    if qs:
        pi = qs[0]
    #logger.debug("qs2: %s" % pformat(qs))
    if not pi:
        pi = PeerInfo.objects.create(info_hash=info_hash,port=port,address=ip)
    #logger.debug("qs3: %s" % pformat(qs))
    if not pi:
        return _err("Unable to establish state")
    
    #logger.debug("state established for %s:%s" % (ip,port))
    
    if request.user and not request.user.is_anonymous():
        pi.user = request.user
        
    DEFNUMWANT = 50
    MAXNUMWANT = 20

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
   
    #logger.debug("save started")
    #logger.debug(event) 
    #logger.debug(pformat(pi))
    pi = pi.save(force_update=True)
    #logger.debug("save done")
    #logger.debug(pformat(pi))
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
    
    dict['complete'] = seeding
    dict['downloaded'] = downloaded
    dict['incomplete'] = count - seeding
    dict['interval'] = 60
    
    if compact:
        if p4str.value:
            dict['peers'] = p4str.raw[:offset]
        if p6str.value:
            dict['peers6'] = p6str.raw[:offset]
            
    #logger.debug("announce: %s:%s (%s): compact=%s, offset=%d, dict=%s" % (ip, port, repr(info_hash), compact, offset, repr(dict)))
    return tracker_response(dict)
    
def tracker_response(dict):
    return HttpResponse(bencode(dict),mimetype="text/plain")

def summarize(qs,entitlement=None):
    count = 0
    downloaded = 0
    seeding = 0
    try:
        for pi in qs:
            if entitlement:
                if not pi.user:
                    continue
                
                profile = user_profile(pi.user)
                if not entitlement in profile.get_entitlements():
                    continue
            
            if pi.state == PeerInfo.STARTED or pi.state == PeerInfo.COMPLETED:
                count = count + 1
                if pi.left == 0:
                    seeding = seeding + 1
                
                if pi.state == PeerInfo.COMPLETED:
                    downloaded = downloaded + 1
    except Exception as e: # Database specific exception
        logger.error("Database unavailable: %s" % e)
        return _err('Database unavailable')
    return count,downloaded,seeding
    
def peer_status(hashvals,entitlement=None):
    files = {}
    for info_hash in hashvals:
        qs = PeerInfo.objects.filter(info_hash=info_hash)
        if entitlement:
            qs = qs.filter(user__profile__entitlements__contains=entitlement) #this is just a course filter - need to verify
        count,downloaded,seeding = summarize(qs,entitlement)
        info_hash = unhexlify(info_hash)
        files[info_hash]= {'complete': seeding, 'downloaded': downloaded, 'incomplete': count - seeding}
    return files
    
def scrape(request,entitlement=None):
    info_hash = None
    if request.GET.has_key('info_hash'):
        info_hash = get_from_qs(request.META['QUERY_STRING'], 'info_hash=')
        #logger.debug("announce: getting hash from request: %s" % request.META['QUERY_STRING'])
    
    if not info_hash:
        return _err("I'm not going to tell you about all torrents n00b!")

    info_hash = hexlify(unquote(info_hash))
    
    return tracker_response({'files': peer_status([info_hash],entitlement)})
    
    
@login_required
def user_announce(request):
    return announce(request)
