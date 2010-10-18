'''
Created on Oct 17, 2010

@author: leifj
'''

from lobber.tracker.models import PeerInfo
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse,\
    HttpResponseForbidden
from deluge.bencode import bencode
from socket import gethostname
from lobber.share.models import Torrent

def announce(request,info_hash=None):
    
    if not info_hash and request.GET.has_key('info_hash'):
        info_hash = request.GET['info_hash']
    
    if not info_hash:
        return HttpResponseBadRequest("Missing info_hash")

    t = Torrent.objects.filter(info_hash=info_hash)[:1]
    if not t:
        return HttpResponseForbidden("Not authorized")

    peer_id = None
    if not request.GET.has_key('peer_id'):
        return HttpResponseBadRequest("Missing peer_id")
    peer_id = request.GET['peer_id']
    
    pi,created = PeerInfo.objects.get_or_create(info_hash=info_hash,peer_id=peer_id)
    
    if request.user and not request.user.is_anonymous:
        pi.user = request.user
        
    addr = request.META['REMOTE_ADDR']
    if '.' in addr:
        pi.ipv4 = addr
    if ':' in addr:
        pi.ipv6 = addr
        
    numwant = 50
    if request.GET.has_key('numwant'):
        numwant = request.GET['numwant']

    for key in ('port','uploaded','downloaded','left','corrupt'):
        if request.GET.has_key(key):
            value = request.GET[key]
            setattr(pi,key,value)
    
    if request.GET.has_key('ipv6'):
        ipv6 = request.GET['ipv6']
        if ':' in ipv6:
            pi.ipv6 = ipv6

    event = None
    if request.GET.has_key('event'):
        event = request.GET['event'] 
    
    if event == 'stopped':
        pi.state = PeerInfo.STOPPED
    elif event == 'completed':
        pi.state = PeerInfo.COMPLETED 
    elif event == 'paused':
        pi.state = PeerInfo.PAUSED  
    elif event == 'started':
        pi.state = PeerInfo.STARTED
    
    pi.save()
    
    dict = {'torrentid': 'lobber-%s' % gethostname(),'peers': []}
    complete = 0
    incomplete = 0
    for pi in PeerInfo.objects.filter(info_hash=info_hash)[:numwant]:
        if pi.state == PeerInfo.COMPLETED:
            complete = complete+1
            incomplete = incomplete+1
            dict['peers'].append(pi.info_dict())
        
    return HttpResponse(bencode(dict),mimetype="text/plain")
    
@login_required
def user_announce(request):
    return announce(request)
