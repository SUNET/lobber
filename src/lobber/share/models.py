from django.db import models
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth
from django.contrib.auth.models import User

class Torrent(models.Model):
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField()
    creator = models.ForeignKey(User)
    creation_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField() # FIXME: Default to something reasonable.
    data = models.FileField(upload_to='torrents') # upload_to: directory in MEDIA_ROOT.
    hashval = models.CharField(max_length=40)
    acl = models.TextField()
    tags = models.ManyToManyField('Tag')

    def __unicode__(self):
        return '%s "%s" (acl=%s)' % (self.hashval, self.name, self.acl)

    def auth(self, username, perm):
        for ace in self.acl.split(' '):
            if ace.startswith('user:%s' % username):
                if ace.endswith('#w'):  # Write permission == all.
                    return True
                if ace.endswith('#%c' % perm):
                    return True
        return False

class Tag(models.Model):
    value = models.CharField(max_length=128, blank=True, primary_key=True)

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
    
            
