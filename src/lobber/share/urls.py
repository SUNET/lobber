from django.conf.urls.defaults import *
urlpatterns = patterns(
    # Prefix function.
    'lobber.share.views',
    # (regexp as a string, function without prefix as a string)
    (r'^$', 'torrent_list'),
    (r'^torrent/(?P<tfile>.+)$', 'torrent_get'),
    (r'^upload/$', 'upload'),
    (r'^upload_f/$', 'torrent_add1'),
    (r'^upload_a/$', 'torrent_add2'),
    (r'^user/$', 'user_view'),
    (r'^(?P<handle_id>\d+)$', 'torrent_view'),
    )
