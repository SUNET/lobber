from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^announce\??(?P<info_hash>.+)$',"lobber.tracker.views.announce"),
    (r'^announce$', "lobber.tracker.views.announce"),
    (r'^scrape$', "lobber.tracker.views.scrape"),
    )
