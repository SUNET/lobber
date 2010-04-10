from django.conf.urls.defaults import *
from lobber.share.torrent import *
from lobber.share.views import *
from lobber.share.links import *

urlpatterns = patterns('',
    # (regexp as a string, function without prefix as a string)
    (r'^$', welcome),
    # RESTful API.
    (r'^torrent/$',TorrentView),
    (r'^torrent/delete/(?P<tid>.+)$',delete_torrent),
    (r'^torrent/sendlink/(?P<tid>.+)$',send_link_mail),
    (r'^torrent/gufrt/(?P<tid>.+)$', gimme_url_for_reading_torrent),
    (r'^torrent/new/$',TorrentForm),
    (r'^torrent/(?P<inst>.*)\.(.+)$', TorrentView),
    (r'^key/$', api_keys),
    (r'^key/(?P<inst>.+)$', api_key),
    (r'^key.html', key_form),
    # Old stuff, pre API era.  FIXME: Clean up.
    (r'^user/$', user_self),          # Short for self.
    (r'^upload/$', upload),
    (r'^ulform/$', TorrentForm),
    )
