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
from pprint import pprint
import struct
from ctypes import create_string_buffer

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

def announce(request,info_hash=None):
    
    if not info_hash and request.GET.has_key('info_hash'):
        info_hash = request.GET['info_hash']
    
    if not info_hash:
        return _err('Missing info_hash')

    info_hash = unquote(info_hash)

    pprint("info_hash=%s" % info_hash)
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
        
    numwant = 50
    if request.GET.has_key('numwant'):
        numwant = int(request.GET['numwant'])
        if numwant > 200:
            numwant = 200
        if numwant < 0:
            numwant = 50

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
    
    dict['complete'] = seeding
    dict['downloaded'] = downloaded
    dict['incomplete'] = count - seeding
    dict['interval'] = 10
    
    if compact:
        if p4str.value:
            dict['peers'] = p4str.value
        if p6str.value:
            dict['peers6'] = p6str.value
            
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
