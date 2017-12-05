import socket
import thread
import pickle

CORE_INIT = False
PORT_OBSERVER = 8000
PORT_NOTIFIER = 8001
HOST = "127.0.0.1"

class Networker(object):
    """
    Abstract base networking class. Implements custom TCP-based protocol
    that allows for relaying TCP messages through an intermediary message
    distributor from a single notifier to multiple observers.
    """
    PACKET_SIZE = 6
    SUBJECT_DELIM = "##"
    SIZE_DELIM = "$$"

    def _net_relay(self, receive_socket, observer_sockets):
        out_data = ""

        while True:
            packet = receive_socket.recv(self.PACKET_SIZE)
            out_data += packet
            if not packet:
                break

        for observer_socket in observer_sockets:
            try:
                # Change to fragmented sends to allow for eval of header
                # w/ subject in observer before sending all the data over
                observer_socket.sendall(out_data)
            except socket.error:
                pass  # Unprepared observer

    def _net_send(self, message, subject):
        send_socket = socket.socket()
        send_socket.connect((self.host, self.port))

        send_data = self._header_write(message, subject)
        send_socket.sendall(send_data)
        send_socket.close()

    def _net_receive(self, subject):
        receive_socket = socket.socket()
        receive_socket.connect((self.host, self.port))

        rcvd_data = ""
        matching_subject = True
        data_size = None

        while data_size is None or len(rcvd_data) < data_size:
            packet = receive_socket.recv(self.PACKET_SIZE)
            rcvd_data += packet

            if (data_size is None) and (self.SUBJECT_DELIM in rcvd_data):
                data_size, notf_subj = self._header_parse(rcvd_data)

                if notf_subj != subject:
                    matching_subject = False
                    break

        receive_socket.close()
        received_message = rcvd_data.split(self.SUBJECT_DELIM, 1)[1]
        return (matching_subject, received_message)

    def _header_parse(self, message_frag):
        header = message_frag.split(self.SUBJECT_DELIM, 1)[0]
        data_size = int(header.split(self.SIZE_DELIM, 1)[0])
        notf_subj = header.split(self.SIZE_DELIM, 1)[1]

        return (data_size, notf_subj)

    def _header_write(self, message, subject):
        data_len = len(message) + len(subject)
        data_len += len(self.SIZE_DELIM) + len(self.SUBJECT_DELIM)
        data_len += len(str(data_len))

        send_data = str(data_len)
        send_data += self.SIZE_DELIM + subject + self.SUBJECT_DELIM + message

        return send_data

class Initialize(Networker):
    """
    Initializes a new system network. Instantiate this object
    once before creating Notifiers or Observers in any modules.
    """
    port_notifier = PORT_NOTIFIER
    port_observer = PORT_OBSERVER
    host = HOST
    observer_sockets = []

    def __init__(self, system):
        self.system = system
        self._init_relay(self.port_observer, self._connect_observer)
        self._init_relay(self.port_notifier, self._connect_notifier)

    def _init_relay(self, port, connection_callback):
        try:
            sock = socket.socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, port))
            sock.listen(5)
            thread.start_new_thread(self._listen, (sock, connection_callback))

        except socket.error, msg:
            print "Socket error (core): " + msg[1]

    def _listen(self, sock, connection_callback):
        while True:
            conn_sock, addr = sock.accept()
            thread.start_new_thread(connection_callback, (conn_sock, addr,))

    def _connect_notifier(self, conn_sock, addr):
        print "Core connected to notifier [" + str(addr[1]) + "]"
        self._net_relay(conn_sock, self.observer_sockets)

    def _connect_observer(self, conn_sock, addr):
        print "Core connected to observer [" + str(addr[1]) + "]"
        self.observer_sockets.append(conn_sock)

class Notifier(Networker):
    """
    Data Notifier.
    """
    host = HOST
    port = PORT_NOTIFIER

    def __init__(self, subject):
        self.subject = subject

    def notify(self, message_object):
        try:
            message = pickle.dumps(message_object)
            self._net_send(message, self.subject)

        except socket.error, msg:
            print "Socket error (notifier): " + msg[1]


class Observer(Networker):
    """
    Data observer.
    """
    host = HOST
    port = PORT_OBSERVER

    def __init__(self, subject, callback):
        self.subject = subject
        self.callback = callback
        thread.start_new_thread(self._observe, ())

    def _observe(self):
        while True:
            try:
                matching_subject, received_data = self._net_receive(self.subject)
                if matching_subject:
                    received_obj = pickle.loads(received_data)
                    self.callback(received_obj)

            except socket.error, msg:
                print "Socket error (observer): " + msg[1]
                break
