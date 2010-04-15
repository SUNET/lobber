import sys
import stomp
from pprint import pprint

def notify(topic,data):
   c = stomp.Connection()
   c.start()
   c.connect()
   c.send(data,destination=topic)
   c.disconnect()

if __name__ == "__main__":
   notify(sys.argv[1],sys.argv[2])
   sys.exit(0)
