from stompservice import StompClientFactory
from orbited import json
import smtplib
import types
from pprint import pprint

class MailSender(StompClientFactory):

    def recv_connected(self, msg):
        self.subscribe("/agents/sendmail")

    def recv_message(self, msg):
        packet = json.decode(msg.get('body'))
        pprint(packet)
        if not type(packet) is types.DictType:
            return

        notify_to = None
        if packet.has_key('notify_to'):
            notify_to = packet.get('notify_to')

        pprint(notify_to)
        try:
            s = smtplib.SMTP()
            s.connect()
            pprint(s)
            s.sendmail(packet.get('sender'),packet.get('to'),packet.get('message'))
            pprint("sent")
            s.quit()
            pprint("done")
            if notify_to != None:
                self.send(notify_to,"Success: !")
        except Exception,e:
            pprint(e)
            if notify_to != None:
                self.send(notify_to,"Error: "+e)
