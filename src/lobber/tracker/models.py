'''
Created on Oct 17, 2010

@author: leifj
'''
from django.db import models
from django.contrib.auth.models import User
import socket
import struct

def _urlesc(s):
    r = ''
    for n in range(0, len(s), 2):
        r += '%%%s' % s[n:n+2].upper()
    return r

class PeerInfo(models.Model):
    COMPLETED = 1
    STARTED = 2
    STOPPED = 3
    PAUSED = 4
    
    user = models.ForeignKey(User,blank=True,null=True,db_index=True)
    info_hash = models.CharField(max_length=128,db_index=True)
    peer_id = models.CharField(max_length=128)
    address = models.IPAddressField(default='127.0.0.1',db_index=True)
    port = models.IntegerField(default=0,db_index=True)
    uploaded = models.BigIntegerField(blank=True,null=True)
    downloaded = models.BigIntegerField(blank=True,null=True)
    left = models.BigIntegerField(blank=True,null=True)
    corrupt = models.IntegerField(blank=True,null=True)
    state = models.SmallIntegerField(blank=True,null=True,choices=((STARTED,"started"),(COMPLETED,"completed"),(STOPPED,"stopped"),(PAUSED,'paused')))
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('info_hash','address','port')
    
    def __unicode__(self):
        return "%s@%s:%s" % (self.eschash(),self.address,self.port)
    
    def dict(self):
        return {'ip': self.address.encode('ascii'),'port': self.port}
    
    def eschash(self):
        return _urlesc(self.info_hash)
    
    def escpeerid(self):
        return _urlesc(self.peer_id)
    
    def pack_peer(self,buf4,buf6,offset):
        family = socket.AF_INET
        fmt="!4sH"
        len=6
        buf = buf4
        if ':' in self.address:
            family = socket.AF_INET6
            fmt="!16sH"
            len=18
            buf = buf6
        
        struct.pack_into(fmt,buf,offset,socket.inet_pton(family,self.address),self.port)
        return len
