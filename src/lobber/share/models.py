from django.db import models
from django.contrib.auth.models import User

# Create your models here.

#class User(models.Model):
#    pass
# http://docs.djangoproject.com/en/dev/topics/auth/#module-django.contrib.auth

class Torrent(models.Model):
    #owner = models.ForeignKey(User)
    name = models.CharField(max_length=128, blank=True)
    data = models.FileField(upload_to='torrents') # Dir in MEDIA_ROOT.
    hashval = models.CharField(max_length=40)
    def __unicode__(self):
        return '%s "%s"' % (self.hashval, self.name)

class Handle(models.Model):
    """A handle is supposed to be published in some way, enabling
    other users to get to the torrent.
    """
    torrent = models.ForeignKey(Torrent)
    name = models.CharField(max_length=1024) # Makes up the URL.
    published = models.BooleanField(default=True)
    creation = models.DateTimeField(auto_now_add=True)
    expiration = models.DateTimeField()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return '/%s/' % self.id
