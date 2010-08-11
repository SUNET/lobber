from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # (regexp as a string, function without prefix as a string)
    (r'^$', "lobber.share.torrent.welcome"),
    ## RESTful API.
    # Torrents.
    (r'^torrent/$',"lobber.share.torrent.TorrentView"),
    (r'^torrent/all.rss$',"lobber.share.torrent.TorrentView"),
    (r'^torrent/search(?:\.(?:[^\.]+))?$',"lobber.share.torrent.search"),
    (r'^torrent/remove/(?P<tid>[0-9]+)\.([^\.]+)$', "lobber.share.torrent.remove_torrent"),
    (r'^torrent/sendlink/(?P<tid>[0-9]+)$',"lobber.share.links.send_link_mail"),
    (r'^torrent/gufrt/(?P<tid>[0-9]+)$', "lobber.share.links.gimme_url_for_reading_torrent"),
    (r'^torrent/add/$',"lobber.share.torrent.TorrentForm"),
    (r'^torrent/jnlp/$',"lobber.share.torrent.upload_jnlp"),
    (r'^torrent/(?P<inst>[0-9]+)(?:\.([^\.]+))?$', "lobber.share.torrent.TorrentView"),
    (r'^torrent/(?P<inst>.+)\.torrent$', "lobber.share.torrent.torrent_by_hashval"),
    (r'^torrent/exists/(?P<inst>.+)$', "lobber.share.torrent.exists"),
    (r'^torrent/scrape/(?P<inst>[0-9]+)\.([^\.]+)$', "lobber.share.torrent.scrape"),
    # Tagging.
    (r'^torrent/tags.json$', "lobber.share.tag.tag_usage"),
    (r'^torrent/tag/(?P<name>.+)\.([^\.]+)$', "lobber.share.tag.list_torrents_for_tag"),
    (r'^torrent/(?P<tid>[0-9]+)/tags(?:\.([^\.]+))?$', "lobber.share.tag.tags"),
    (r'^torrent/tag/gufrt/(?P<tagstr>.+)', "lobber.share.links.gimme_url_for_reading_tag"),
    # ACL handling.
    (r'^torrent/(?P<tid>.+)/ace/add/(?P<ace>.+)$', "lobber.share.acl.add_ace"),
    (r'^torrent/(?P<tid>.+)/ace/remove/(?P<ace>.+)$', "lobber.share.acl.remove_ace"),
    (r'^torrent/(?P<tid>.+)/ace$', "lobber.share.acl.edit"),
    # Constraints.
    (r'^key/(?P<key>.+)/constraint/add/url/(?P<pattern>.+)$', "lobber.share.constraint.add_urlfilter"),
    (r'^key/(?P<key>.+)/constraint/remove/url/(?P<pattern>.+)$', "lobber.share.constraint.remove_urlfilter"),
    (r'^key/(?P<key>.+)/constraint/add/tag/(?P<tag>.+)$', "lobber.share.constraint.add_tagconstraint"),
    (r'^key/(?P<key>.+)/constraint/remove/tag/(?P<tag>.+)$', "lobber.share.constraint.remove_tagconstraint"),
    # Keys
    (r'^key(?:\.[^\.]+)?$',"lobber.share.keys.keys"),
    # The user.
    (r'^user/$',"lobber.share.users.user_self"),
    (r'^user/ace_subjects$',"lobber.share.users.ace_subjects"),
    )
