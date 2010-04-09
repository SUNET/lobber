from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from lobber.settings import MEDIA_ROOT
admin.autodiscover()

urlpatterns = patterns('',
    (r'^auth/',include('lobber.auth.urls')),
    (r'^admin/', include('admin.site.urls')),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
    	{'document_root': MEDIA_ROOT}),
    (r'', include('lobber.share.urls')),
)
