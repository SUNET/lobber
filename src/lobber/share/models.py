from django.db import models
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth
from django.contrib.auth.models import User

class Torrent(models.Model):
    name = models.CharField(max_length=256, blank=True)
    creation = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=True)
    expiration = models.DateTimeField()
    data = models.FileField(upload_to='torrents') # upload_to: directory in MEDIA_ROOT.
    hashval = models.CharField(max_length=40)
    acl = models.TextField()
    tags = models.ManyToManyField('Tag')

    def __unicode__(self):
        return '%s "%s" (%s)' % (self.hashval, self.name, self.owner.username)

    def auth(self, username, perm):
        for ace in self.acl.split(' '):
            if ace.startswith('user:%s' % username):
                if ace.endswith('#w'):  # Write permission == all.
                    return True
                if ace.endswith('#%c' % perm):
                    return True
        return False

class Tag(models.Model):
    value = models.CharField(max_length=64, blank=True, primary_key=True)

class Key(models.Model):
    secret = models.CharField(max_length=64, primary_key=True)
    entitlements = models.TextField()         # Space separated entls.
    urlfilter = models.TextField()            # Space separated simplified regexps.
    comment = models.CharField(max_length=64) # F.ex. user (for audit trail).

class UserProfile(models.Model):
    entitlements = models.TextField()
    display_name = models.CharField(max_length=256, blank=True)
    user = models.ForeignKey(User, unique=True)
