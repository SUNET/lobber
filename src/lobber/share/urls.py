from django.conf.urls.defaults import *
urlpatterns = patterns(
    # Prefix function.
    'lobber.share.views',
    # (regexp as a string, function without prefix as a string)
    (r'^$', 'torrent_list'),
    # RESTful API.
    (r'^torrent/$', 'api_torrents'),
    (r'^torrent/(?P<inst>.+)$', 'api_torrent'),
    (r'^key/$', 'api_keys'),
    (r'^key/(?P<inst>.+)$', 'api_key'),
    (r'^key.html', 'key_form'),
    # Old stuff, pre API era.  FIXME: Clean up.
    (r'^user/$', 'user_self'),          # Short for self.
    (r'^upload/$', 'upload'),
    (r'^ulform/$', 'upload_form'),
    (r'^(?P<handle_id>\d+)$', 'torrent_view'),
    )
