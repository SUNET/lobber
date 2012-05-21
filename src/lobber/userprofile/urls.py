from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    # Constraints.
    (r'^key/(?P<key>.+)/constraint/add/url/(?P<pattern>.+)$', "lobber.userprofile.views.add_urlfilter"),
    (r'^key/(?P<key>.+)/constraint/remove/url/(?P<pattern>.+)$', "lobber.userprofile.views.remove_urlfilter"),
    (r'^key/(?P<key>.+)/constraint/add/tag/(?P<tag>.+)$', "lobber.userprofile.views.add_tagconstraint"),
    (r'^key/(?P<key>.+)/constraint/remove/tag/(?P<tag>.+)$', "lobber.userprofile.views.remove_tagconstraint"),
    # Keys
    (r'^key/add',"lobber.userprofile.views.addkey"),
    (r'^key(?:\.[^\.]+)?$',"lobber.userprofile.views.listkeys"),
    (r'^key/(?P<key>[\w]+)/remove$',"lobber.userprofile.views.removekey"),
    # The user.
    (r'^$',"lobber.userprofile.views.user_self"),
    (r'^ace_subjects$',"lobber.userprofile.views.ace_subjects"),
    )
