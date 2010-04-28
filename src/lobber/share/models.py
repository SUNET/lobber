from django.db import models
from django.core.exceptions import ObjectDoesNotExist
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth
from django.contrib.auth.models import User
from lobber.settings import TORRENTS,BASE_URL
import tagging
from tagging.models import Tag

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
        return "/torrent/%s.torrent" % self.hashval

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
            tagconstraintsok_flag = True
            if profile.tagconstraints:
                tagconstraintsok_flag = False
                c = profile.tagconstraints.split()
                for tag in Tag.objects.get_for_object(self):
                    if tag.name in c:
                        tagconstraintsok_flag = True
                        break
            if not tagconstraintsok_flag:
                #print 'DEBUG: tag constraints not ok for %s with tag constraints %s, seeking #%c for torrrent %s' % (user, profile.tagconstraints, perm, self)
                return False

        for ace in self.acl.split():
            for username in usernames:
                # FIXME: ace must start with username, not the other way around!
                #
                # The result is that if USER creates a key with
                # entitlement user:USER:key:blurb, the key user will
                # be able to act as USER wrt to ACL checks.
                #
                # I changed this 2010-04-26 because I was confused.
                # Now I don't want to change it back until we have an API for adding ace:s.
                if username.startswith(ace.split('#')[0]):
                    if ace.endswith('#w'):  # Write permission == all.
                        return True
                    if ace.endswith('#%c' % perm):
                        return True
        #print 'DEBUG: perm %s denied for %s on %s' % (perm, user, self)
        return False
    
    def authz_tag(self, user, perm, tag):
        """Does USER have PERM on torrent w.r.t. tagging operations on
        the torrent with TAG?
        """
        if perm == 'r':
            return self.authz(user, tag)
        elif perm == 'w' or perm == 'd':
            if self.authz(user, 'w'):
                if ':' in tag:       # Non-global tags are restricted.
                    p = None
                    try:
                        p = user.profile.get()
                    except ObjectDoesNotExist:
                        pass
                    if p and tag in p.entitlements:
                        return True
                else:
                    return True
        #print 'DEBUG: perm %s denied for %s on %s for %s' % (perm, user, self, tag)
        return False

    def add_ace(self, user, ace):
        """Add ACE to ACL of self, prepended by 'user:<username>'
        where username is the name of USER.

        Return resulting ace on success.
        """
        fullace = 'user:%s:%s' % (user.username, ace)
        if not acl.valid_ace_p(fullace):
            return None
        self.acl += fullace
        return fullace

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
    urlfilter = models.TextField(blank=True) # Space separated list of regexps.
    tagconstraints = models.TextField(blank=True) # Space separated list of tags.
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
