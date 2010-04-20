from django.db import models
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth
from django.contrib.auth.models import User
from lobber.settings import TORRENTS
import tagging
from tagging.models import Tag
from pprint import pprint

class Torrent(models.Model):
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User)
    creation_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField() # FIXME: Default to something reasonable.
    data = models.FileField(upload_to='.') # upload_to: directory in TORRENTS.
    hashval = models.CharField(max_length=40)
    acl = models.TextField()

    def __unicode__(self):
        return '%s "%s" (acl=%s)' % (self.hashval, self.name, self.acl)

    def url(self):
        return "/torrents/%s.torrent" % self.hashval

    def auth(self, username, perm):
        for ace in self.acl.split(' '):
            if ace.startswith('user:%s' % username):
                if ace.endswith('#w'):  # Write permission == all.
                    return True
                if ace.endswith('#%c' % perm):
                    return True
        return False
    
    def authz_tag(self,user,perm,tagname):
        return True

    def add_ace(self, ace):
        self.acl += ace

    def file(self):
        fn = '%s/%s.torrent' % (TORRENTS, self.hashval)
        f = None
        try:
            f = file(fn)
        except IOError, e:
            if e[0] == 2:               # ENOENT
                raise
            else:
                raise
        return f

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, related_name='profile')
    creator = models.ForeignKey(User)
    display_name = models.CharField(max_length=256, blank=True)
    entitlements = models.TextField(blank=True) # Space separated entls.
    urlfilter = models.TextField() # Space separated simplified regexps.
    expiration_date = models.DateTimeField(null=True)

    def __unicode__(self):
        return '%s (%s), entl="%s", filter="%s"' % (self.display_name,
                                                    self.user,
                                                    self.entitlements,
                                                    self.urlfilter)
    def get_username(self):
        username = self.user.username
        if username.startswith('key:'):
            username = username[4:]
        return username
    
            
tagging.register(Torrent)
