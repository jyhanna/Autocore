import socket
import thread
import logging
import protocol

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)


class Relay(object):
    """
    Initializes a relay core to allow intermediate processing
    between notifier and observer sockets. Responsibilities
    include listening to notifications and observer connection
    requests. When a notification must be broadcasted, the
    currently listening observers with matching subjects
    are relayed the message.
    """
    observers = {}

    def __init__(self, system, port_notifier, port_observer, host):
        self.system = system
        self.port_notifier = port_notifier
        self.port_observer = port_observer
        self.host = host

        if not self._core_running():
            self._init_relay(self.port_observer, self._connect_observer)
            self._init_relay(self.port_notifier, self._connect_notifier)

    def _core_running(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.host, self.port_observer))
        sock.close()
        return result == 0

    def _init_socket(self, port):
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, port))
        sock.listen(5)
        return sock

    def _init_relay(self, port, connection_callback):
        try:
            sock = self._init_socket(port)
            thread.start_new_thread(self._listen, (sock, connection_callback))

        except socket.error, msg:
            logger.warn("Socket error (core): " + msg[1])

    def _listen(self, sock, connection_callback):
        while True:
            conn_sock, addr = sock.accept()
            thread.start_new_thread(connection_callback, (conn_sock, addr,))

    def _connect_notifier(self, conn_sock, addr):
        logger.info("Core connected to notifier [" + str(addr[1]) + "]")
        self._relay(conn_sock)

    def _connect_observer(self, conn_sock, addr):
        logger.info("Core connected to observer [" + str(addr[1]) + "]")
        self._evaluate_observer(conn_sock)

    def _evaluate_observer(self, receive_socket):
        _, subject = protocol.receive(receive_socket)
        if subject in self.observers:
            self.observers[subject].append(receive_socket)
        else:
            self.observers[subject] = [receive_socket]

    def _relay(self, receive_socket):
        message, notifier_subject = protocol.receive(receive_socket)

        for observer_subject in self.observers:
            if observer_subject == notifier_subject:
                for observer_sock in self.observers[observer_subject]:
                    try:
                        protocol.send(observer_sock, message, notifier_subject)
                    except socket.error:
                        pass  # Unprepared observer


class Send(object):
    """
    Broadcasts a notification. Objects can be serialized
    """
    def __init__(self, message, subject, serializer, port, host):
        send_socket = socket.socket()
        send_socket.connect((host, port))

        protocol.send(send_socket, serializer(message), subject)
        send_socket.close()


class Receive(object):
    """
    Observes for a specific notification.
    """
    def __init__(self, subject, callback, deserializer, port, host):
        receive_socket = socket.socket()
        receive_socket.connect((host, port))

        protocol.send(receive_socket, "", subject)
        message, _ = protocol.receive(receive_socket)

        callback(deserializer(message))
        receive_socket.close()
