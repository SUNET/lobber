from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from lobber.settings import ADMIN_MEDIA_ROOT, MEDIA_ROOT, TORRENTS
admin.autodiscover()

urlpatterns = patterns('',
    (r'^auth/',include('lobber.auth.urls')),
    (r'^admin-media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': ADMIN_MEDIA_ROOT}),
    (r'^admin/', include(admin.site.urls)),
    (r'^site-media/(?P<path>.*)$', 'django.views.static.serve',
    	{'document_root': MEDIA_ROOT}),
    (r'^torrents/(?P<path>.+\.torrent)$', 'django.views.static.serve',
        {'document_root': TORRENTS}),
    (r'',include('lobber.share.urls'))
)
