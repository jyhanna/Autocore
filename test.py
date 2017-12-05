import time
import network

class TestMsgObject(object):

    def __init__(self, tattr):
        self.test_attrib = tattr


def notifier_tester():
    notifier = network.Notifier("/test/subject")
    message = "Test Message...##abcd<<"
    notifier.notify(message)
    notifier.notify(message)
    time.sleep(1.0)
    notifier.notify(TestMsgObject(20))

def observer_tester():
    network.Observer("/test/subject", observer_callback)
    #network.Observer("/test/subdject", observer_callback)

def observer_callback(data):
    print "Callback data: ", data.test_attrib

network.Initialize("test_mod2ule")
observer_tester()
notifier_tester()

while True:
    time.sleep(0.9)
