from django.db import models
from django.core.exceptions import ObjectDoesNotExist
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth
from django.contrib.auth.models import User
from lobber.settings import TORRENTS,BASE_URL, LOBBER_LOG_FILE
import tagging
from tagging.models import Tag
from lobber.torrenttools import bdecode
import os
from lobber.notify import notifyJSON
import shutil
import lobber.log
from lobber.userprofile.models import user_profile
from django_co_acls.models import is_allowed, is_anyone_allowed

logger = lobber.log.Logger("web", LOBBER_LOG_FILE)

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
    hashval = models.CharField(max_length=40,db_index=True)
    
    effective_rights = None

    def __unicode__(self):
        return '%s (%d / %s) (expire=%s)' % \
               (self.name, self.id, self.hashval, self.expiration_date)

    def url(self):
        return "/torrent/%d.torrent" % self.id
    
    def eschash(self):
        return _urlesc(self.hashval)

    def abs_url(self):
        return "%s%s" % (BASE_URL,self.url())

    def compute_effective_rights(self,user,profile=None):
        self.effective_rights = {}
        for perm in ['r','w','d']:
            if self.authz_i(user,perm,profile):
                self.effective_rights[perm] = True
            else:
                self.effective_rights[perm] = False
        return self

    def authz(self,user,perm,profile=None):
        if not self.effective_rights:
            self.compute_effective_rights(user,profile)
        
        if perm == 'd':
            return self.effective_rights['d'] or self.effective_rights['w']
        elif perm == 'r':
            return self.effective_rights['r'] or self.effective_rights['w']
        else:   
            return self.effective_rights['w']

    # very quick way to determine if a torrent is public read
    def is_public_read(self):
        return is_anyone_allowed(self, 'r')

    def authz_i(self, user, perm, profile=None):
        """Does USER have PERM on torrent?"""
        if not profile:
            profile = user_profile(user)
        
        if profile:
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

        return is_allowed(self, user, perm)
    
    # XXX entitlements stuff must go
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

    def readable_tags(self, user):
        return filter(lambda tag: self.authz_tag(user, "r", tag.name),
                      Tag.objects.get_for_object(self))

    def file(self):
        fn = '%s/%d.torrent' % (TORRENTS, self.id)
        if not os.path.exists(fn):
            for t in Torrent.objects.filter(hashval=self.hashval):
                fnold = '%s/%s.torrent' % (TORRENTS, t.hashval)
                fnnew = '%s/%d.torrent' % (TORRENTS, t.id)
                shutil.copy(fnold, fnnew)
            os.unlink('%s/%s.torrent' % (TORRENTS, self.hashval))
                
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
        try:
            os.unlink(self.file().name)
        except IOError, e:
            if e[0] == 2:               # ENOENT
                pass            
        id = self.id
        hashval = self.hashval
        self.delete()
        notifyJSON("/torrents/notify",{'delete': [id,hashval]})

tagging.register(Torrent)
