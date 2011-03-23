from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'^$',"lobber.share.views.show"),
    (r'^all.rss$',"lobber.share.views.show"),
    (r'^all.json$',"lobber.share.views.show"),
    (r'^search(?:\.(?:[^\.]+))?$',"lobber.share.views.search"),
    (r'^remove/(?P<tid>[0-9]+)(?:\.([^\.]+))?$', "lobber.share.views.remove_torrent"),
    (r'^start-lobber-client.jnlp$',"lobber.share.views.upload_jnlp"),
    (r'^add(?:\.(?:[^\.]+))?$',"lobber.share.views.add_torrent"),
    (r'^(?P<inst>[0-9]+)(?:\.([^\.]+))?$', "lobber.share.views.show"),
    (r'^(?P<inst>.+)\.torrent$', "lobber.share.views.torrent_by_hashval"),
    (r'^exists/(?P<inst>.+)$', "lobber.share.views.exists"),
    (r'^scrape/(?P<inst>[^\.]+)\.([^\.]+)$', "lobber.share.views.scrape"),
    (r'^scrapehash/(?P<hash>[^\.]+)(?:\.(?:[^\.]+))?$', "lobber.share.views.scrape_hash"),
    # Tagging.
    (r'^tags.json$', "lobber.share.tag.tag_usage"),
    (r'^tag/(?P<name>.+)\.([^\.]+)$', "lobber.share.views.list_torrents_for_tag"),
    (r'^(?P<tid>[0-9]+)/tags(?:\.([^\.]+))?$', "lobber.share.views.tags"),
    # ACL handling.
    (r'^(?P<tid>.+)/ace/add/(?P<ace>.+)(?:\.(?:[^\.]+))?$', "lobber.share.views.add_ace"),
    (r'^(?P<tid>.+)/ace/remove/(?P<ace>.+)(?:\.(?:[^\.]+))?$', "lobber.share.views.remove_ace"),
    (r'^(?P<tid>.+)/ace$', "lobber.share.views.edit"),
    )
