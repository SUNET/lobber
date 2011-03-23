from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'^$',"lobber.share.torrent.show"),
    (r'^all.rss$',"lobber.share.torrent.show"),
    (r'^all.json$',"lobber.share.torrent.show"),
    (r'^search(?:\.(?:[^\.]+))?$',"lobber.share.torrent.search"),
    (r'^remove/(?P<tid>[0-9]+)(?:\.([^\.]+))?$', "lobber.share.torrent.remove_torrent"),
    (r'^start-lobber-client.jnlp$',"lobber.share.torrent.upload_jnlp"),
    (r'^add(?:\.(?:[^\.]+))?$',"lobber.share.torrent.add_torrent"),
    (r'^(?P<inst>[0-9]+)(?:\.([^\.]+))?$', "lobber.share.torrent.show"),
    (r'^(?P<inst>.+)\.torrent$', "lobber.share.torrent.torrent_by_hashval"),
    (r'^exists/(?P<inst>.+)$', "lobber.share.torrent.exists"),
    (r'^scrape/(?P<inst>[^\.]+)\.([^\.]+)$', "lobber.share.torrent.scrape"),
    (r'^scrapehash/(?P<hash>[^\.]+)(?:\.(?:[^\.]+))?$', "lobber.share.torrent.scrape_hash"),
    # Tagging.
    (r'^tags.json$', "lobber.share.tag.tag_usage"),
    (r'^tag/(?P<name>.+)\.([^\.]+)$', "lobber.share.tag.list_torrents_for_tag"),
    (r'^(?P<tid>[0-9]+)/tags(?:\.([^\.]+))?$', "lobber.share.tag.tags"),
    # ACL handling.
    (r'^(?P<tid>.+)/ace/add/(?P<ace>.+)(?:\.(?:[^\.]+))?$', "lobber.share.acl.add_ace"),
    (r'^(?P<tid>.+)/ace/remove/(?P<ace>.+)(?:\.(?:[^\.]+))?$', "lobber.share.acl.remove_ace"),
    (r'^(?P<tid>.+)/ace$', "lobber.share.acl.edit"),
    )
