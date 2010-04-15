from twisted.application import service
application = service.Application("SMTP Mail Agent")
from twisted.application import internet
from lobber.agent.sendmail import MailSender

stompClientService = internet.TCPClient('localhost',61613,MailSender())
stompClientService.setServiceParent(application)
