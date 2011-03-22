from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from lobber.settings import ADMIN_MEDIA_ROOT, MEDIA_ROOT
from django.http import HttpResponseRedirect
admin.autodiscover()

def welcome(req):
    return HttpResponseRedirect("/torrent/")

urlpatterns = patterns('',
    (r'^$', welcome),
    (r'^index.html$',welcome),
    (r'^auth/',include('lobber.auth.urls')),
    (r'^admin-media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': ADMIN_MEDIA_ROOT}),
    (r'^admin/', include(admin.site.urls)),
    (r'^site-media/(?P<path>.*)$', 'django.views.static.serve',
    	{'document_root': MEDIA_ROOT}),
    (r'^tracker/',include('lobber.tracker.urls')),
    (r'^link/',include('lobber.links.urls')),
    (r'^user/',include('lobber.userprofile.urls')),
    (r'^torrent/',include('lobber.share.urls')),
)
