from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'^login-federated/$', 'lobber.auth.views.login_federated'),
    (r'^login/$', 'lobber.auth.views.login'),
    (r'^logout/$', 'lobber.auth.views.logout'),
    )
