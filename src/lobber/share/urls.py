from django.conf.urls.defaults import *
urlpatterns = patterns('lobber.share.views',
    (r'^$', 'torrent_list'),
    (r'^(?P<handle>.+)/$', 'torrent_view'),
)
