import sys

from twisted.mail.smtp import SMTPSenderFactory
from twisted.python.usage import Options, UsageError
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor
from lobber.settings import SMTP_HOST,SMTP_PORT

def sendmail(sender,to,message):
   """
   @param from: the sender address
   @para to: the recipient address
   @param message: message text
   """

   d = Deferred()
   senderFactory = SMTPSenderFactory(sender,to,message,d) 
   host = SMTP_HOST
   if host == None:
      host = 'localhost'
   port = SMTP_PORT
   if port == None:
      port = 587
   reactor.connectTCP(host,port,senderFactory)
   return d
