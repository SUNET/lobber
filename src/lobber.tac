
import sys
import os

from twisted.web import server,wsgi
from twisted.python import threadpool
from twisted.internet import reactor
from twisted.application import internet,service
from django.core.handlers.wsgi import WSGIHandler

sys.path.append("lobber")
os.environ['DJANGO_SETTINGS_MODULE'] = 'lobber.settings'

def wsgi_resource():
    pool = threadpool.ThreadPool()
    pool.start()
    # Allow Ctrl-C to get you out cleanly:
    reactor.addSystemEventTrigger('after', 'shutdown', pool.stop)
    wsgi_resource = wsgi.WSGIResource(reactor, pool, WSGIHandler())
    return wsgi_resource

wsgi_root = wsgi_resource()

application = service.Application('lobber')
internet.TCPServer(8080,server.Site(wsgi_root)).setServiceParent(application)
