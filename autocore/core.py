#! /usr/bin/env python
import thread
import pickle
import network

PORT_OBSERVER = 8000
PORT_NOTIFIER = 8001
HOST = "127.0.0.1"

# Change to module-level logger
logger = network.logger


class Initialize(object):
    """
    Initializes a new system network. Instantiate this object
    once before creating Notifiers or Observers in any modules.
    When initializing multiple times (eg. across independent modules
    running simultaneously), subsequent initializations will have
    no effect. This means the first `Initialize()` call from the first
    running module will launch the network's core.
    """
    def __init__(self, module):
        network.Relay(module, PORT_NOTIFIER, PORT_OBSERVER, HOST)


class Notifier(object):
    """
    Provides a directed notification mechanism through which objects
    can be sent. All observers listening on a notifier's subject will
    recieve a notification.
    """
    host = HOST
    port = PORT_NOTIFIER

    def __init__(self, subject):
        self.subject = subject

    def notify(self, message_object):
        network.Send(message_object,
                     self.subject,
                     pickle.dumps,
                     self.port,
                     self.host)


class Observer(object):
    """
    Provides an observation mechanism for modules to listen
    to incoming notifications of the Observer's subject.
    """
    host = HOST
    port = PORT_OBSERVER

    def __init__(self, subject, callback):
        self.subject = subject
        self.callback = callback
        thread.start_new_thread(self._observe, ())

    def _observe(self):
        while True:
            network.Receive(self.subject,
                            self.callback,
                            pickle.loads,
                            self.port,
                            self.host)
