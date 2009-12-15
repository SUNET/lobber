from django.db import models
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth
from django.contrib.auth.models import User

class Torrent(models.Model):
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=256, blank=True)
    #tags = models.ManyToManyFields(Tag)

    data = models.FileField(upload_to='torrents') # Dir in MEDIA_ROOT.
    hashval = models.CharField(max_length=40)

    def __unicode__(self):
        return '%s "%s" (%s)' % (self.hashval, self.name, self.owner.username)

class Tag(models.Model):
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=256, blank=True)
    torrents = models.ManyToManyFields(Torrent)

class Key(models.Model):
    owner = models.ForeignKey(User)
    secret = models.CharField(max_length=256, primary_key=True)
    acl = models.ForeignKey(ACL)
    comment = models.CharField(max_length=64) # F.ex. user (for audit trail).

class ACL(models.Model):
    acs = models.TextField()    


# class Handle(models.Model):
#     """A handle is supposed to be published in some way, enabling
#     other users to get to the torrent.
#     """
#     torrent = models.ForeignKey(Torrent)
#     name = models.CharField(max_length=1024) # Makes up the URL.
#     published = models.BooleanField(default=True)
#     creation = models.DateTimeField(auto_now_add=True)
#     expiration = models.DateTimeField()
#
#     def __unicode__(self):
#         return self.name
#
#     def get_absolute_url(self):
#         return '/%s/' % self.id

