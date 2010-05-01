from stompservice import StompClientFactory
from orbited import json
import smtplib
import types
from pprint import pprint
from django.utils.http import urlquote

class PipeHeater(StompClientFactory):

    def recv_connected(self, msg):
        self.subscribe("/torrent/add")

    def recv_message(self, msg):
        infohash = json.decode(msg.get('body'))
    
        try:
            httplib.HTTPConnection(TRACKER_ADDR).request('GET', urlquote('/announce?info_hash'+hash))
        except:
            pass
