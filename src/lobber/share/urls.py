from django.conf.urls.defaults import *
from lobber.share.keys import api_keys, api_key, key_form
from lobber.share.links import send_link_mail, gimme_url_for_reading_torrent
from lobber.share.torrent import TorrentView, delete_torrent, upload_jnlp, TorrentForm, exists, welcome
from lobber.share.users import user_self
from lobber.share.tag import list_tags, add_tag, remove_tag, get_tags, list_torrents_for_tag

urlpatterns = patterns('',
    # (regexp as a string, function without prefix as a string)
    (r'^$', welcome),
    # RESTful API.
    (r'^torrent/$',TorrentView),
    (r'^torrent/all.rss$',TorrentView),
    (r'^torrent/delete/(?P<tid>[0-9]+)$',delete_torrent),
    (r'^torrent/sendlink/(?P<tid>[0-9]+)$',send_link_mail),
    (r'^torrent/gufrt/(?P<tid>[0-9]+)$', gimme_url_for_reading_torrent),
    (r'^torrent/new/$',TorrentForm),
    (r'^torrent/jnlp/$',upload_jnlp),
    (r'^torrent/(?P<inst>[0-9]+)\.([^\.]+)$', TorrentView),
    (r'^torrent/exists/(?P<inst>.+)$', exists),
    (r'^key/$', api_keys),
    (r'^key/(?P<inst>.+)$', api_key),
    (r'^key.html', key_form),
    # Tagging
    (r'^torrent/tags$', list_tags),
    (r'^torrent/tag/(?P<name>.+)\.([^\.]+)$', list_torrents_for_tag),
    (r'^torrent/(?P<tid>.+)/tag/add/(?P<name>.+)$', add_tag),
    (r'^torrent/(?P<tid>.+)/tag/remove/(?P<name>.+)$', remove_tag),
    (r'^torrent/(?P<tid>.+)/tags$', get_tags),
    # Old stuff, pre API era.  FIXME: Clean up.
    (r'^user/$', user_self), # Short for self.
    )
