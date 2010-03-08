from django.conf.urls.defaults import *
urlpatterns = patterns(
    # Prefix function.
    'lobber.share.views',
    # (regexp as a string, function without prefix as a string)
    (r'^$', 'TorrentsView'),
    # RESTful API.
    (r'^torrent/$', 'TorrentsView'),
    (r'^torrent/(?P<inst>.+)$', 'TorrentView'),
    (r'^key/$', 'api_keys'),
    (r'^key/(?P<inst>.+)$', 'api_key'),
    (r'^key.html', 'key_form'),
    # Old stuff, pre API era.  FIXME: Clean up.
    (r'^user/$', 'user_self'),          # Short for self.
    (r'^upload/$', 'upload'),
    (r'^ulform/$', 'TorrentForm'),
    (r'^gufrt/(?P<tid>.+)$', 'gimme_url_for_reading_torrent'),
    (r'^(?P<tid>\d+)$', 'torrent_view'),
    )
