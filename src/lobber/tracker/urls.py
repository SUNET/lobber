from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'^announce\??(?P<info_hash>.+)$',"lobber.tracker.views.announce"),
    (r'^announce$', "lobber.tracker.views.announce"),
    (r'^uannounce$', "lobber.tracker.views.user_announce"),
    (r'^scrape$', "lobber.tracker.views.scrape"),
    )
