from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #(r'^nordushare/', include('nordushare.foo.urls')),
    (r'^nordushare/$', 'filbunke.share.views.torrent_list'),
    (r'^nordushare/(?P<handle>.+)/$', 'filbunke.share.views.torrent_view'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),
)
