from django.conf.urls.defaults import *
urlpatterns = patterns(
    # Prefix function.
    'lobber.share.views',
    # (regexp as a string, function without prefix as a string)
    (r'^$', 'torrent_list'),
    (r'^torrent/(?P<tfile>.+)$', 'torrent_get'),
    (r'^upload/$', 'upload'),
    (r'^ulform/$', 'upload_form'),
    (r'^user/$', 'user_view'),
    (r'^(?P<handle_id>\d+)$', 'torrent_view'),
    )
