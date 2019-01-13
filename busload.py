""" Qt Widget which can view the busload in a graph.
"""

from PySide2.QtCharts import QtCharts
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import Qt


class BusLoadWidget(QtWidgets.QWidget):
    def __init__(self, can_connection):
        super().__init__()
        self._messages = []

        layout = QtWidgets.QVBoxLayout()
        self.chart_view = QtCharts.QChartView()
        layout.addWidget(self.chart_view)
        self.setLayout(layout)

        # Construct graph:
        self.chart = QtCharts.QChart()
        self.chart_view.setChart(self.chart)
        self.busload_series = QtCharts.QLineSeries()
        self.busload_series.setName("Busload")
        pen = QtGui.QPen(Qt.red)
        pen.setWidth(3)
        self.busload_series.setPen(pen)
        self.chart.addSeries(self.busload_series)
        self.load_axis = QtCharts.QValueAxis()
        self.load_axis.setRange(0, 100000)
        self.load_axis.setTickCount(6)
        self.load_axis.setTitleText("Load")
        self.chart.setAxisY(self.load_axis, self.busload_series)
        self.time_axis = QtCharts.QDateTimeAxis()
        self.time_axis.setTitleText("Time")
        self.time_axis.setFormat("HH:mm:ss.zzz")
        self.time_axis.setTickCount(5)
        now = QtCore.QDateTime.currentDateTime()
        self.time_axis.setRange(now.addMSecs(-100), now.addMSecs(100))
        self.chart.setAxisX(self.time_axis, self.busload_series)

        self._prev_time = now
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(500)

        can_connection.message_received.connect(self.on_message)

    def on_message(self, message):
        self._messages.append(message)

    def on_timer(self):
        # Okay, bucket all incoming messages.
        bits = sum(m.bitsize() for m in self._messages)
        self._messages = []
        now = QtCore.QDateTime.currentDateTime()
        timespan = self._prev_time.msecsTo(now) * 0.001
        self._prev_time = now
        x = now.toMSecsSinceEpoch()
        if timespan > 0:
            bps = bits / timespan
        else:
            bps = 0
        self.busload_series.append(x, bps)
        self.time_axis.setMax(now)
