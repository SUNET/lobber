# Start dev
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# End dev
from django.conf.urls import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.http import HttpResponseRedirect
admin.autodiscover()

def welcome(req):
    return HttpResponseRedirect("/torrent/")

urlpatterns = patterns('',
    (r'^$', welcome),
    (r'^index.html$',welcome),
    (r'^auth/',include('lobber.auth.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^tracker/',include('lobber.tracker.urls')),
    (r'^link/',include('lobber.links.urls')),
    (r'^user/',include('lobber.userprofile.urls')),
    (r'^torrent/',include('lobber.share.urls')),
)

# Start dev
urlpatterns += staticfiles_urlpatterns()
# End dev