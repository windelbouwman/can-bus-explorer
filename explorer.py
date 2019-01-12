""" CAN bus explorer GUI.

A PyQt5 based CAN bus explorer utility.

"""

import datetime
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
import struct
import logging
import socket
import threading

logger = logging.getLogger("can-explorer")


class CanMessage:
    """ Represents a single can message. """

    def __init__(self, id, data, timestamp=None):
        self.id = id
        self.data = data
        self.timestamp = timestamp

    @property
    def hexdata(self):
        """ Return shiny hexadecimal data """
        b = ["{:02X}".format(b) for b in self.data]
        return " ".join(b)

    def __str__(self):
        return "CAN msg ID={:X} LEN={} DATA={}".format(
            self.id, len(self.data), self.hexdata
        )


class MessageLogModel(QtCore.QAbstractTableModel):
    """ A can message model.

    Contains a log of messages.

    Columns include:
    - timestamp
    - ID
    - data
    """

    def __init__(self, can_connection):
        super().__init__()
        self.can_connection = can_connection

        # List of title, property, column width tuples:
        self._headers = [
            ("Time of msg", "timestamp", 100),
            ("ID", "id", 30),
            ("DATA bytes", "hexdata", 80),
        ]
        self._messages = []
        can_connection.message_received.connect(self.on_message)

    def on_message(self, message):
        logger.debug("Add message in model %s", message)
        parent = QtCore.QModelIndex()
        row = len(self._messages)
        self.beginInsertRows(parent, row, row)
        self._messages.append(message)
        self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self._messages = []
        self.endResetModel()

    def rowCount(self, parent):
        return len(self._messages)

    def columnCount(self, parent):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            header = self._headers[section]
            if role == Qt.DisplayRole:
                return header[0]
            elif role == Qt.SizeHintRole:
                width = header[2]
                # TODO?
                # print(width)
                # return QtCore.QSize(width, 1)

    def data(self, index, role):
        if not index.isValid():
            return

        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()
            prop_name = self._headers[column][1]
            message = self._messages[row]
            value = str(getattr(message, prop_name))
            return value


class CanInterface:
    def __init__(self):
        self._recv_subscribers = []

    def attach_recv_callback(self, callback):
        self._recv_subscribers.append(callback)

    def _recv(self, message):
        for callback in self._recv_subscribers:
            callback(message)

    def connect(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()

    def send(self, message):
        raise NotImplementedError()


class DummyCanLink(CanInterface):
    """ Simple dummy which does local echo. """

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send(self, message):
        timestamp = datetime.datetime.now().ctime()
        new_message = CanMessage(message.id, message.data, timestamp=timestamp)
        self._recv(new_message)


class SocketCanLink(CanInterface):
    """ Socket can interface.

    Links:
    http://www.bencz.com/hacks/2016/07/10/python-and-socketcan/
    """

    fmt = "<IB3x8s"

    def connect(self):
        interface = "vcan0"
        self.sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        self.sock.bind((interface,))
        # Spin receiver thread:
        self._running = True
        self.recv_thread = threading.Thread(
            target=self.recv_process, name="socketcan-recv"
        )
        self.recv_thread.start()

    def disconnect(self):
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
            timestamp = datetime.datetime.now().ctime()
            message = CanMessage(can_id, data, timestamp=timestamp)
            print(message)
            self._recv(message)
        logger.info("Receiver thread finished")


class CanConnection(QtCore.QObject):
    """ A can connection hub.

    Use this class to communicate over CAN.
    """

    connection_opened = QtCore.pyqtSignal(bool)
    connection_closed = QtCore.pyqtSignal(bool)
    message_received = QtCore.pyqtSignal(CanMessage)

    def __init__(self, can_link):
        super().__init__()
        self.can_link = can_link
        self.can_link.attach_recv_callback(self._on_message)
        self._connected = False

    @QtCore.pyqtProperty(bool)
    def is_connected(self):
        return self._connected

    def _set_connected(self, state):
        self._connected = state
        self.connection_opened.emit(state)
        self.connection_closed.emit(not state)

    def open(self):
        logger.info("Open connection")
        self.can_link.connect()
        self._set_connected(True)

    def close(self):
        logger.info("Close connection")
        self.can_link.disconnect()
        self._set_connected(False)

    def send(self, message):
        if self._connected:
            logger.info("sending message %s", message)
            self.can_link.send(message)
        else:
            logger.error("Error, not connected")

    def _on_message(self, message):
        self.message_received.emit(message)


class ConnectionWidget(QtWidgets.QWidget):
    """ A widget to open and close a connection. """

    def __init__(self, can_connection):
        super().__init__()
        self.can_connection = can_connection
        layout = QtWidgets.QVBoxLayout()

        self.open_button = QtWidgets.QPushButton("Open")
        self.open_button.setEnabled(not can_connection.is_connected)
        can_connection.connection_closed.connect(self.open_button.setEnabled)
        self.open_button.clicked.connect(self.on_open)
        layout.addWidget(self.open_button)

        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.on_close)
        self.close_button.setEnabled(can_connection.is_connected)
        can_connection.connection_opened.connect(self.close_button.setEnabled)
        layout.addWidget(self.close_button)
        layout.addStretch()
        self.setLayout(layout)

    def on_open(self):
        self.can_connection.open()

    def on_close(self):
        self.can_connection.close()


class SendMessageWidget(QtWidgets.QWidget):
    """ A Widget to construct messages and send them. """

    def __init__(self, can_connection):
        super().__init__()
        self.can_connection = can_connection
        can_connection.connection_opened.connect(self.setEnabled)
        self.setEnabled(can_connection.is_connected)
        layout = QtWidgets.QVBoxLayout()

        # Message construction panel:
        grid_layout = QtWidgets.QGridLayout()

        # Id:
        id_label = QtWidgets.QLabel("ID (hex)")
        grid_layout.addWidget(id_label, 0, 0)
        self.id_edit = QtWidgets.QLineEdit("11")
        self.id_edit.setInputMask("Hhhhh")
        grid_layout.addWidget(self.id_edit, 1, 0)

        # Length:
        length_label = QtWidgets.QLabel("Length")
        grid_layout.addWidget(length_label, 0, 1)
        self.length_edit = QtWidgets.QLineEdit("6")
        grid_layout.addWidget(self.length_edit, 1, 1)

        # Data:
        data_label = QtWidgets.QLabel("Data:")
        grid_layout.addWidget(data_label, 0, 2, 1, 8)
        self.data_edits = []
        for i in range(8):
            data_label = QtWidgets.QLabel(str(i))
            data_label.setAlignment(Qt.AlignCenter)
            grid_layout.addWidget(data_label, 2, 2 + i)
            data_edit = QtWidgets.QLineEdit("{:02X}".format(i + 1))
            data_edit.setInputMask("HH")
            grid_layout.addWidget(data_edit, 1, 2 + i)
            self.data_edits.append(data_edit)

        layout.addLayout(grid_layout)
        self.send_button = QtWidgets.QPushButton("Send!")
        layout.addWidget(self.send_button)
        layout.addStretch()

        # layout_horizontal = QtWidgets.QHBoxLayout()
        # layout_horizontal.addLayout(layout)
        # layout_horizontal.addStretch()
        self.setLayout(layout)

        # Connect signals:
        self.send_button.clicked.connect(self.on_send)

    def on_send(self):
        can_message = self.create_can_message()
        self.can_connection.send(can_message)

    def create_can_message(self):
        """ Create a nice can message based on given inputs. """
        try:
            id = int(self.id_edit.text(), 16)
            size = int(self.length_edit.text())
            assert size >= 0
            if size > 8:
                size = 8
            data = bytearray()
            for i in range(size):
                b = int(self.data_edits[i].text(), 16)
                data.append(b)
            data = bytes(data)
        except ValueError as ex:
            print("Invalid data!", ex)
        else:
            can_message = CanMessage(id, data)
            return can_message


class MessageLogWidget(QtWidgets.QWidget):
    """ A widget with a history of can messages. """

    def __init__(self, can_connection):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.clear_button = QtWidgets.QPushButton("Clear!")
        self.clear_button.clicked.connect(self.on_clear)
        layout.addWidget(self.clear_button)
        self.table_view = QtWidgets.QTableView()
        layout.addWidget(self.table_view)
        self.setLayout(layout)

        self.message_model = MessageLogModel(can_connection)
        self.table_view.setModel(self.message_model)

    def on_clear(self):
        self.message_model.clear()


class CanExplorer(QtWidgets.QMainWindow):
    """ Main window for the CAN explorer.

    Components:
    - CAN connection manager
    - Send can message
    - Message log
    """

    def __init__(self):
        super().__init__()

        # can_link = DummyCanLink()
        can_link = SocketCanLink()
        self.can_connection = CanConnection(can_link)

        self.setWindowTitle("CAN bus explorer")

        # Connection dock widget:
        self.connection_widget = ConnectionWidget(self.can_connection)
        self.connection_dock_widget = QtWidgets.QDockWidget("Connection")
        self.connection_dock_widget.setWidget(self.connection_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connection_dock_widget)

        # Message sending widget dock:
        self.send_message_widget = SendMessageWidget(self.can_connection)
        self.send_message_dock_widget = QtWidgets.QDockWidget("Send")
        self.send_message_dock_widget.setWidget(self.send_message_widget)
        self.addDockWidget(
            Qt.DockWidgetArea.TopDockWidgetArea, self.send_message_dock_widget
        )

        # Add message log dock widget:
        self.message_log_widget = MessageLogWidget(self.can_connection)
        self.message_log_dock_widget = QtWidgets.QDockWidget("Messages")
        self.message_log_dock_widget.setWidget(self.message_log_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.message_log_dock_widget)


def main():
    logformat = "%(asctime)s | %(levelname)8s | %(name)10.10s | %(message)s"
    logging.basicConfig(level=logging.INFO, format=logformat)
    app = QtWidgets.QApplication(sys.argv)
    main_window = CanExplorer()
    main_window.show()
    app.exec_()


if __name__ == "__main__":
    main()
