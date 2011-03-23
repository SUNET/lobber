'''
Created on Mar 22, 2011

@author: leifj
'''
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth.models import User

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
    
def request_user_profile(request):
    profile = request.session.get('lobber_userprofile',None)
    if not profile:
        profile = user_profile(request.user)
        request.session['lobber_userprofile'] = profile
    return profile
    
    return profile
    
def user_profile(user,default=True):
        try:
            return user.profile.get();
        except ObjectDoesNotExist:
            if default:
                return UserProfile(user=user,creator=user)
            else:
                return None