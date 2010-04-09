from django.conf.urls.defaults import *

urlpatterns = patterns('lobber.auth.authn',
    (r'^login-federated/$', 'login_federated'),
    (r'^login/$', 'login'),
    (r'^logout/$', 'logout'),
    )
