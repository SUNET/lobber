from django.conf.urls.defaults import patterns

urlpatterns = patterns('lobber.auth.authn',
    (r'^login-federated/$', 'login_federated'),
    (r'^login/$', 'login'),
    (r'^logout/$', 'logout'),
    )
