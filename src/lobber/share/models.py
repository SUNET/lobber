from django.db import models
from django.core.exceptions import ObjectDoesNotExist
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth
from django.contrib.auth.models import User
from lobber.settings import TORRENTS,BASE_URL
import tagging
from tagging.models import Tag
from deluge.bencode import bdecode
import os
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey
from oauth_provider.models import Consumer

def _urlesc(s):
    r = ''
    for n in range(0, len(s), 2):
        r += '%%%s' % s[n:n+2].upper()
    return r

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
        return '%s (%d / %s) (acl=%s) (expire=%s)' % \
               (self.name, self.id, self.hashval, self.acl,
                self.expiration_date)

    def url(self):
        return "/torrent/%d.torrent" % self.id
    
    def eschash(self):
        return _urlesc(self.hashval)

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
            ace_user, ace_perm = ace.split('#')
            #print 'DEBUG: ace_user: %s, ace_perm: %s, usernames: %s' % (ace_user, ace_perm, usernames)
            for username in usernames:
                if not ace_user or ace_user.startswith(username):
                    if ace_perm == 'w': # Write permission == all.
                        return True
                    if ace_perm == '%c' % perm:
                        return True
        #print 'DEBUG: perm %s denied for %s on %s' % (perm, user, self)
        return False
    
    def authz_tag(self, user, perm, tag):
        """Does USER have PERM on torrent w.r.t. tagging operations on
        the torrent with TAG?
        """
        if perm == 'r':
            return self.authz(user, perm)
        elif perm == 'w' or perm == 'd':
            if self.authz(user, 'w'):
                if ':' in tag:       # Non-global tags are restricted.
                    p = None
                    try:
                        p = user.profile.get()
                    except ObjectDoesNotExist:
                        pass
                    if p and tag in p.get_entitlements():
                        return True
                else:
                    return True
        #print 'DEBUG: perm %s denied for %s on %s for %s' % (perm, user, self, tag)
        return False

    def authz_acl(self, user, perm):
        "Does USER have PERM on torrent w.r.t. its ACL?"
        if perm in 'rw':
            return self.authz(user, perm)
        return False                

    def get_acl(self, user):
        if not self.authz_acl(user, 'r'):
            return []
        return list(self.acl.split())

    def set_acl(self, user, aces):
        if not self.authz_acl(user, 'w'):
            return False
        self.acl = ' '.join(aces)
        return self.acl

    def add_ace(self, user, ace):
        """
        Add ACE to ACL of self.  Return True on success, False if
        permission is denied.
        """
        acl = self.get_acl(user)
        if not ace in acl:
            acl = self.set_acl(user, acl+[ace])
        return acl
    
    def remove_ace(self, user, ace):
        """
        Remove ACE from ACL of self.
        Return False if permission is denied, otherwise True.
        """
        aces = self.get_acl(user)
        if ace in aces:
            aces.remove(ace)
            return self.set_acl(user, aces)
        return True

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
    
    def meta_info(self):
        data = self.file().read()
        return bdecode(data)['info']
    
    def remove(self):
        Tag.objects.update_tags(self,None)
        os.unlink(self.file().name)
        self.delete();

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
        return '%s (%s), entl="%s", filter="%s", tagconstraints="%s"' \
               % (self.display_name,
                  self.user,
                  self.entitlements,
                  self.urlfilter,
                  self.tagconstraints)

    def get_username(self):
        username = self.user.username
        if username.startswith('key:'):
            username = username[4:]
        return username

    def get_entitlements(self):
        return list(self.entitlements.split())

    ### URL-filter.
    def get_urlfilter(self, user):
        if not self.authz(user):
            return False
        return list(self.urlfilter.split())

    def set_urlfilter(self, user, flt):
        if not self.authz(user):
            return False
        self.urlfilter = ' '.join(flt)
        return self.urlfilter

    def add_urlfilter(self, user, flt):
        f = self.get_urlfilter(user)
        if not flt in f:
            return self.set_urlfilter(user, f + [flt])
        return f

    def remove_urlfilter(self, user, flt):
        """
        Remove FLT from self.urlfilter.

        Return False if permission is denied, otherwise the removed
        element or True if the element wasn't present.
        """
        f = self.get_urlfilter(user)
        if not flt in f:
            return True
        f.remove(flt)
        if not self.set_urlfilter(user, f):
            return False
        return flt

    ### Tag constraints.
    # FIXME: Behold the pattern -- same as the url filter stuff!  Do
    # something about it, please.
    def get_tagconstraint(self, user):
        if not self.authz(user):
            return False
        return list(self.tagconstraints.split())

    def set_tagconstraint(self, user, tag):
        if not self.authz(user):
            return False
        self.tagconstraints = ' '.join(tag)
        return self.tagconstraints

    def add_tagconstraint(self, user, tag):
        t = self.get_tagconstraint(user)
        if not tag in t:
            return self.set_tagconstraint(user, t + [tag])
        return t
            
    def remove_tagconstraint(self, user, tag):
        """
        Remove TAG from self.tagconstraints.

        Return False if permission is denied, otherwise True.
        element or True if the element wasn't present.
        """
        t = self.get_tagconstraint(user)
        if not tag in t:
            return True
        t.remove(tag)
        if not self.set_tagconstraint(user, t):
            return False
        return tag

    ### Authz.
    def authz(self, user):
        try:
            profile = user.profile.get()
        except ObjectDoesNotExist:
            return False
        for entl in profile.get_entitlements():
            if entl == 'user:' + self.creator.username:
                return True
        return False
    
def user_profile(user,default=True):
        try:
            return user.profile.get();
        except ObjectDoesNotExist:
            if default:
                return UserProfile(user=user,creator=user)
            else:
                return None

tagging.register(Torrent)
