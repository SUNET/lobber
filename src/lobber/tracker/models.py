'''
Created on Oct 17, 2010

@author: leifj
'''
from django.db import models
from django.contrib.auth.models import User

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
    
    user = models.ForeignKey(User,blank=True,null=True)
    info_hash = models.CharField(max_length=128)
    peer_id = models.CharField(max_length=128)
    ipv4 = models.IPAddressField(null=True,blank=True)
    ipv6 = models.IPAddressField(null=True,blank=True)
    port = models.IntegerField(null=True,blank=True)
    uploaded = models.IntegerField(blank=True,null=True)
    downloaded = models.IntegerField(blank=True,null=True)
    left = models.IntegerField(blank=True,null=True)
    currupt = models.IntegerField(blank=True,null=True)
    state = models.SmallIntegerField(blank=True,null=True,choices=((STARTED,"started"),(COMPLETED,"completed"),(STOPPED,"stopped"),(PAUSED,'paused')))
    last_seen = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return "%s %d for %s" % (self.ip(),self.port,self.info_hash)
    
    def ip(self):
        if self.ipv6:
            return self.ipv6
        else:
            return self.ipv4
    
    def pidict(self):
        return {'peer id': self.peer_id,'ip': self.ip(),'port': self.port}