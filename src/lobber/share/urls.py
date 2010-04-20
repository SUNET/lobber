from django.conf.urls.defaults import *
from lobber.share.keys import api_keys, api_key, key_form
from lobber.share.links import send_link_mail, gimme_url_for_reading_torrent
from lobber.share.torrent import TorrentView, delete_torrent, upload_jnlp, TorrentForm, exists, welcome
from lobber.share.users import user_self
from lobber.share.tag import list_tags, add_tag, remove_tag, get_tags

urlpatterns = patterns('',
    # (regexp as a string, function without prefix as a string)
    (r'^$', welcome),
    # RESTful API.
    (r'^torrent/$',TorrentView),
    (r'^torrent/delete/(?P<tid>.+)$',delete_torrent),
    (r'^torrent/sendlink/(?P<tid>.+)$',send_link_mail),
    (r'^torrent/gufrt/(?P<tid>.+)$', gimme_url_for_reading_torrent),
    (r'^torrent/new/$',TorrentForm),
    (r'^torrent/jnlp/$',upload_jnlp),
    (r'^torrent/(?P<inst>.*)\.(.+)$', TorrentView),
    (r'^torrent/exists/(?P<inst>.*)$', exists),
    (r'^key/$', api_keys),
    (r'^key/(?P<inst>.+)$', api_key),
    (r'^key.html', key_form),
    # Tagging
    (r'^torrent/tags$', list_tags),
    (r'^torrent/(?P<tid>.+)/tag/add/(?P<name>.+)$', add_tag),
    (r'^torrent/(?P<tid>.+)/tag/remove/(?P<name>.+)$', remove_tag),
    (r'^torrent/(?P<tid>.+)/tags$', get_tags),
    # Old stuff, pre API era.  FIXME: Clean up.
    (r'^user/$', user_self), # Short for self.
    )
