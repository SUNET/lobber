from django.db import models
from django.core.exceptions import ObjectDoesNotExist
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth
from django.contrib.auth.models import User
from lobber.settings import TORRENTS,BASE_URL
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

    def abs_url(self):
        return "%s%s" % (BASE_URL,self.url())

    def authz(self, user, perm):
        """Does USER have PERM on torrent?"""
        usernames = ['user:%s' % user.username]
        profile = None
        try:
            profile = user.profile.get()
        except ObjectDoesNotExist:
            pass
        if profile:
            usernames += profile.entitlements.split()
        
        for ace in self.acl.split():
            for username in usernames:
                if username.startswith(ace.split('#')[0]):
                    if ace.endswith('#w'):  # Write permission == all.
                        return True
                    if ace.endswith('#%c' % perm):
                        return True
        return False
    
    def authz_tag(self, user, perm, tag):
        """Does USER have PERM on torrent w.r.t. tagging operations on
        the torrent with TAG?
        """
        if perm == 'r':
            return self.authz(user, tag)
        elif perm == 'w' or perm == 'd':
            if self.authz(user, 'w'):
                if ':' in tag:
                    p = None
                    try:
                        p = user.profile.get()
                    except ObjectDoesNotExist:
                        pass
                    if p and tag in p.entitlements:
                        return True
                else:
                    return True
        return False

    def add_ace(self, ace):
        self.acl += ace

    def readable_tags(self, user):
        return filter(lambda tag: self.authz_tag(user, "r", tag.name),
                      Tag.objects.get_for_object(self))

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
    """This is how we represent a key, as well as an ordinary user."""
    user = models.ForeignKey(User, unique=True, related_name='profile')
    creator = models.ForeignKey(User)   # Important for key users.
    display_name = models.CharField(max_length=256, blank=True)
    entitlements = models.TextField(blank=True) # Space separated entls.
    urlfilter = models.TextField(blank=True) # Space separated simplified regexps.
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

    def get_entitlements(self):
        return list(self.entitlements.split(' '))
            
tagging.register(Torrent)
