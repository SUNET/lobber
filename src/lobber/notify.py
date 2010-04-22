import sys
import stomp
import json

def notify(topic,data):
    c = stomp.Connection()
    c.start()
    c.connect()
    c.send(data,destination=topic)
    c.disconnect()

def notifyJSON(topic,data):
    notify(topic,json.dumps(data))

if __name__ == "__main__":
    notifyJSON(sys.argv[1],sys.argv[2])
    sys.exit(0)
