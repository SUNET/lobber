'''
Created on Oct 23, 2010

@author: leifj
'''
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'(?P<pid>[0-9]+)/tag/(?P<tag>.+)$','lobber.links.views.show_tag_link'),
    (r'(?P<pid>[0-9]+)/torrent/(?P<tid>[0-9]+)$','lobber.links.views.show_torrent_link'),
    (r'(?P<pid>[0-9]+)/torrent/(?P<tid>[0-9]+)/message$','lobber.links.views.send_link_mail'),
    (r'tag/(?P<tag>.+)$', "lobber.links.views.link_to_tag"),
    (r'torrent/(?P<tid>[0-9]+)$', "lobber.links.views.link_to_torrent"),
    )