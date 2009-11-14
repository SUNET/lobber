from django.conf.urls.defaults import *
urlpatterns = patterns(
    'lobber.share.views',               # Prefixing function.
    (r'^$', 'torrent_list'),
    (r'^new/$', 'upload'),
    (r'^upload/$', 'torrent_add'),
    (r'^(?P<handle_id>\d+)/$', 'torrent_view'),
    (r'^upload/$', 'torrent_add'),
    )
