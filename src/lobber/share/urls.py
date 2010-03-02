from django.conf.urls.defaults import *
urlpatterns = patterns(
    # Prefix function.
    'lobber.share.views',
    # (regexp as a string, function without prefix as a string)
    (r'^$', 'torrent_list'),
    # RESTful API.
    (r'^torrent/$', 'api_torrents'),
    (r'^torrent/(?P<inst>.+)$', 'api_torrent'),
    #(r'^tag/', 'api_tags')
    #(r'^tag/(?P<inst>.+)$', 'api_tag'),
    #
    (r'^user/$', 'user_self'),          # Short for self.
    (r'^upload/$', 'upload'),
    (r'^ulform/$', 'upload_form'),
    (r'^(?P<handle_id>\d+)$', 'torrent_view'),
    )
