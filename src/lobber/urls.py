from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from lobber.share import auth
from lobber.settings import MEDIA_ROOT
admin.autodiscover()

urlpatterns = patterns('',
    (r'^nordushare/login-federated/$', 'lobber.share.auth.login_federated'),
    (r'^nordushare/login/$', 'lobber.share.auth.login'),
    (r'^nordushare/logout/$', 'lobber.share.auth.logout'),
    (r'^nordushare/', include('lobber.share.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
    	{'document_root': MEDIA_ROOT}),
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
)
