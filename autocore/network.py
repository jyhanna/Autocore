#! /usr/bin/env python
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
    def __init__(self, module, port_notifier, port_observer, host):
        self.observers = {}
        self.module = module
        self.port_notifier = port_notifier
        self.port_observer = port_observer
        self.host = host
        self.max_connections = 10

        if not self._core_running():
            self._init_relay(self.port_observer, self._connect_observer)
            self._init_relay(self.port_notifier, self._connect_notifier)

    def _core_running(self):
        """
        Returns whether or not a core is already running.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.host, self.port_observer))
        sock.close()
        return result == 0

    def _init_relay(self, port, connection_callback):
        """
        Initializes one end of the relay connection, determined by the
        specified port. This should be invoked twice across two different
        ports for incoming (notification) connections, as well as (outgoing)
        (observation) connections in order to set up the relay core server.
        """
        try:
            sock = self._init_socket(port)
            thread.start_new_thread(self._listen, (sock, connection_callback))

        except socket.error, msg:
            logger.warn("Socket error (core): " + msg[1])

    def _init_socket(self, port):
        """
        Sets up the socket for a given relay connection.
        """
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, port))
        sock.listen(self.max_connections)
        return sock

    def _listen(self, sock, connection_callback):
        """
        Listens to incomming connections on a given socket,
        invoking the appropriate connection handler.
        """
        while True:
            conn_sock, addr = sock.accept()
            thread.start_new_thread(connection_callback, (conn_sock, addr,))

    def _connect_notifier(self, conn_sock, addr):
        """
        Notifier connection handler.
        """
        logger.info("Core connected to notifier [" + str(addr[1]) + "]")
        self._relay(conn_sock)

    def _connect_observer(self, conn_sock, addr):
        """
        Observer connection handler.
        """
        logger.info("Core connected to observer [" + str(addr[1]) + "]")
        self._evaluate_observer(conn_sock)

    def _evaluate_observer(self, receive_socket):
        """
        Evaluates a connection to an observer, adding it to the
        list of observers according to its subject.
        """
        _, subject = protocol.receive(receive_socket)
        if subject in self.observers:
            self.observers[subject].append(receive_socket)
        else:
            self.observers[subject] = [receive_socket]

    def _relay(self, receive_socket):
        """
        Relays a signal, initiated by a notification, to the
        appropriate observers.
        """
        message, notifier_subject = protocol.receive(receive_socket)

        for observer_subject in self.observers:
            if observer_subject == notifier_subject:
                for observer_sock in self.observers[observer_subject]:
                    try:
                        protocol.send(observer_sock, message, notifier_subject)
                        # Remove observer socket since it's only created
                        # for one-time use.
                        self.observers[observer_subject].remove(observer_sock)
                    except socket.error, msg:
                        # Unprepared observer
                        logger.warn("Socket error (core): " + msg[1])


class Send(object):
    """
    Broadcasts a notification. Objects can be serialized
    """
    def __init__(self, message, subject, serializer, port, host):
        try:
            send_socket = socket.socket()
            send_socket.connect((host, port))

            protocol.send(send_socket, serializer(message), subject)
            send_socket.close()
        except socket.error, msg:
            logger.warn(str(msg[1]) + "Did you Initialize() to start the core?")


class Receive(object):
    """
    Observes for a specific notification.
    """
    def __init__(self, subject, callback, deserializer, port, host):
        try:
            receive_socket = socket.socket()
            receive_socket.connect((host, port))

            protocol.send(receive_socket, "", subject)
            message, _ = protocol.receive(receive_socket)
        except socket.error, msg:
            logger.warn(str(msg[1]) + " Did you Initialize() to start the core?")
            return

        deserialized_data = deserializer(message)

        try:
            callback(deserialized_data)
        except AttributeError:
            logger.warn("Invalid attribute for msg type: " +
                        str(type(deserialized_data)) + ". "
                        "Were you expecting a different object message type?")

        receive_socket.close()
