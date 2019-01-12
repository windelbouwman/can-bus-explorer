""" Abtraction around different CAN interfaces.
"""

import struct
import datetime
import socket
import threading
import logging
import queue


logger = logging.getLogger("can-explorer")


class CanInterface:
    """ Interface for CAN links. """

    def __init__(self):
        self._recv_subscribers = []
        self._recv_queue = queue.Queue(maxsize=100)

    def attach_recv_callback(self, callback):
        self._recv_subscribers.append(callback)

    def _recv(self, message):
        if not self._recv_queue.full():
            self._recv_queue.put(message)

        for callback in self._recv_subscribers:
            callback(message)

    def connect(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()

    def send(self, message):
        raise NotImplementedError()

    def recv(self):
        """ Blocks until a message is received. """
        return self._recv_queue.get()


class DummyCanLink(CanInterface):
    """ Simple dummy which does local echo. """

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send(self, message):
        timestamp = datetime.datetime.now()
        new_message = CanMessage(message.id, message.data, timestamp=timestamp)
        self._recv(new_message)


class SocketCanLink(CanInterface):
    """ Socket can interface.

    Links:
    http://www.bencz.com/hacks/2016/07/10/python-and-socketcan/
    """

    fmt = "<IB3x8s"

    def __init__(self, interface):
        super().__init__()
        self.interface = interface

    def connect(self):
        self.sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        logger.info("Opening device %s", self.interface)
        self.sock.bind((self.interface,))
        # Spin receiver thread:
        self._running = True
        self.recv_thread = threading.Thread(
            target=self.recv_process, name="socketcan-recv"
        )
        self.recv_thread.start()

    def disconnect(self):
        logger.info("Closing can device")
        self.sock.close()
        self._running = False
        self.recv_thread.join()

    def send(self, message):
        data = struct.pack(self.fmt, message.id, len(message.data), message.data)
        self.sock.send(data)

    def recv_process(self):
        logger.info("Receiver thread started")
        while self._running:
            # Block:
            data = self.sock.recv(16)
            assert len(data) == 16
            can_id, size, data = struct.unpack(self.fmt, data)
            can_id &= socket.CAN_EFF_MASK
            data = data[:size]
            timestamp = datetime.datetime.now()
            message = CanMessage(can_id, data, timestamp=timestamp)
            self._recv(message)
        logger.info("Receiver thread finished")


class CanMessage:
    """ Represents a single can message. """

    def __init__(self, id, data, timestamp=None):
        self.id = id
        self.data = data
        self.timestamp = timestamp

    @property
    def fancytimestamp(self):
        if self.timestamp is None:
            return ""
        else:
            # return self.timestamp.strftime('%A %d %B %Y %H:%M:%S.%f')
            return self.timestamp.strftime("%H:%M:%S.%f")

    @property
    def age(self):
        if self.timestamp is None:
            age = 0.0
        else:
            now = datetime.datetime.now()
            age = now - self.timestamp
            age = age.total_seconds()
        return age

    @property
    def hexdata(self):
        """ Return shiny hexadecimal data """
        b = ["{:02X}".format(b) for b in self.data]
        return " ".join(b)

    def __str__(self):
        return "CAN msg ID={:X} LEN={} DATA={} {}".format(
            self.id, len(self.data), self.hexdata, self.fancytimestamp
        )
