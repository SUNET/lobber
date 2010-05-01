from django.conf.urls.defaults import *
from lobber.share.keys import api_keys, key_form
from lobber.share.links import send_link_mail, gimme_url_for_reading_torrent, gimme_url_for_reading_tag
from lobber.share.torrent import TorrentView, delete_torrent, upload_jnlp, TorrentForm, exists, welcome, torrent_by_hashval
from lobber.share.users import user_self
from lobber.share.tag import list_tags, list_assigned_tags, add_tag, remove_tag, get_tags, list_torrents_for_tag
from lobber.share.acl import add_ace, remove_ace
from lobber.share.constraint import add_urlfilter, add_tagconstraint, remove_urlfilter, remove_tagconstraint

urlpatterns = patterns('',
    # (regexp as a string, function without prefix as a string)
    (r'^$', welcome),
    ## RESTful API.
    # Torrents.
    (r'^torrent/$',TorrentView),
    (r'^torrent/all.rss$',TorrentView),
    (r'^torrent/delete/(?P<tid>[0-9]+)$',delete_torrent),
    (r'^torrent/sendlink/(?P<tid>[0-9]+)$',send_link_mail),
    (r'^torrent/gufrt/(?P<tid>[0-9]+)$', gimme_url_for_reading_torrent),
    (r'^torrent/add/$',TorrentForm),
    (r'^torrent/jnlp/$',upload_jnlp),
    (r'^torrent/(?P<inst>[0-9]+)\.([^\.]+)$', TorrentView),
    (r'^torrent/(?P<inst>.+)\.torrent$', torrent_by_hashval),
    (r'^torrent/exists/(?P<inst>.+)$', exists),
    # Tagging.
    (r'^torrent/tags$', list_tags),
    (r'^torrent/tags/assigned$', list_assigned_tags),
    (r'^torrent/tag/(?P<name>.+)\.([^\.]+)$', list_torrents_for_tag),
    (r'^torrent/(?P<tid>.+)/tag/add/(?P<name>.+)$', add_tag),
    (r'^torrent/(?P<tid>.+)/tag/remove/(?P<name>.+)$', remove_tag),
    (r'^torrent/(?P<tid>.+)/tags$', get_tags),
    (r'^tag/gufrt/(?P<tagstr>.+)', gimme_url_for_reading_tag),
    # ACL handling.
    (r'^torrent/(?P<tid>.+)/ace/add/(?P<ace>.+)$', add_ace),
    (r'^torrent/(?P<tid>.+)/ace/remove/(?P<ace>.+)$', remove_ace),
    # Constraints.
    (r'^key.html', key_form),
    (r'^key/(?P<key>.+)/constraint/add/url/(?P<pattern>.+)$', add_urlfilter),
    (r'^key/(?P<key>.+)/constraint/remove/url/(?P<pattern>.+)$', remove_urlfilter),
    (r'^key/(?P<key>.+)/constraint/add/tag/(?P<tag>.+)$', add_tagconstraint),
    (r'^key/(?P<key>.+)/constraint/remove/tag/(?P<tag>.+)$', remove_tagconstraint),
    (r'^key/$', api_keys),
    # Old stuff, pre API era.  FIXME: Clean up.
    (r'^user/$', user_self), # Short for self.
    )
