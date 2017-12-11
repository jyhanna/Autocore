#! /usr/bin/env python
"""
Simple TCP-based protocol. The format of each discrete message
is: `size`$$`subject`##`payload`.
"""
SUBJECT_DELIM = "##"
SIZE_DELIM = "$$"
PACKET_SIZE = 6


def receive(socket):
    """
    Receives data from a connection on the given socket. Data
    is received and unpacked according to the rules of the
    protocol, ultimately returning the payload as well as the subject.
    """
    rcvd_data = ""
    subject = True
    data_size = None

    while data_size is None or len(rcvd_data) < data_size:
        packet = socket.recv(PACKET_SIZE)
        rcvd_data += packet

        if (data_size is None) and (SUBJECT_DELIM in rcvd_data):
            data_size, subject = _unpack_header(rcvd_data)

    received_message = _split_header(rcvd_data)[1]
    return received_message, subject


def send(socket, message, subject):
    """
    Sends data using the given socket, packing the message
    and subject according to the protocol. The data is packaged
    with the total message size, the subject, and the payload.
    """
    data_len = len(message) + len(subject)
    data_len += len(SIZE_DELIM) + len(SUBJECT_DELIM)
    data_len += len(str(data_len))

    send_data = str(data_len)
    send_data += SIZE_DELIM + subject + SUBJECT_DELIM + message
    socket.sendall(send_data)


def _unpack_header(message_frag):
    """
    Helper for unpacking the header of a message conforming
    to the protocol, returning the size of the message as well
    as the subject.
    """
    header = _split_header(message_frag)[0]
    data_size = int(header.split(SIZE_DELIM, 1)[0])
    notf_subj = header.split(SIZE_DELIM, 1)[1]

    return (data_size, notf_subj)


def _split_header(message):
    """
    Splits the header of a message conforming to the protocol
    from the payload.
    """
    return message.split(SUBJECT_DELIM, 1)
