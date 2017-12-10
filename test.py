import time
import core

class TestMsgObject(object):

    def __init__(self, tattr):
        self.test_attrib = tattr

def notifier_tester():
    notifier = core.Notifier("/test/subject")
    message = "Test Message..."
    notifier.notify(message)
    notifier.notify(message)
    time.sleep(1.0)
    #notifier.notify(TestMsgObject(20))

def observer_tester():
    core.Observer("/test/subject", observer_callback)
    #core.Observer("/test/subdject", observer_callback)

def observer_callback(data):
    print "Callback data: ", data

core.Initialize("test_mod2ule")
core.Initialize("test_mod2ule")
core.Initialize("test_mod2ule")
observer_tester()
notifier_tester()

while True:
    #core.Initialize("test_mod2ule")
    time.sleep(1.0)
    #notifier_tester()
