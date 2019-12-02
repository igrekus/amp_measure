from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QModelIndex

from instrumentcontroller import InstrumentController
from connectionwidget import ConnectionWidget
from measuremodel import MeasureModel
from measurewidget import MeasureWidgetWithSecondaryParameters


class MainWindow(QMainWindow):

    instrumentsFound = pyqtSignal()
    sampleFound = pyqtSignal()
    measurementFinished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_QuitOnClose)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # create instance variables
        self._ui = uic.loadUi('mainwindow.ui', self)
        self._instrumentController = InstrumentController(parent=self)
        self._connectionWidget = ConnectionWidget(parent=self, controller=self._instrumentController)
        self._measureWidget = MeasureWidgetWithSecondaryParameters(parent=self, controller=self._instrumentController)
        self._measureModel = MeasureModel(parent=self, controller=self._instrumentController)

        # init UI
        self._ui.layInstrs.insertWidget(0, self._connectionWidget)
        self._ui.layInstrs.insertWidget(1, self._measureWidget)

        self._init()

    def _init(self):
        self._connectionWidget.connected.connect(self.on_instrumens_connected)
        self._connectionWidget.connected.connect(self._measureWidget.on_instrumentsConnected)

        self._measureWidget.measureComplete.connect(self._measureModel.update)

        self._ui.tableMeasure.setModel(self._measureModel)

        self.refreshView()

    # UI utility methods
    def refreshView(self):
        self.resizeTable()

    def resizeTable(self):
        self._ui.tableMeasure.resizeRowsToContents()
        self._ui.tableMeasure.resizeColumnsToContents()

    # event handlers
    def resizeEvent(self, event):
        self.refreshView()

    @pyqtSlot()
    def on_instrumens_connected(self):
        print(f'connected {self._instrumentController}')

    @pyqtSlot(QModelIndex)
    def on_tableControl_clicked(self, index):
        col = index.column()
        if col in (0, 1):
            return
        secondary = self._measureWidget._selectedSecondaryParam
        point_params = self._controlModel.getParamsForRow(index.row(), secondary)
        self._ui.tableControl.setEnabled(False)
        self._instrumentController.tuneToPoint(
            point_params,
            self._measureWidget._selectedSecondaryParam,
            harmNum=col - 1,
            power=self._ui.comboPow.currentText()[:2]
        )
        self._ui.tableControl.setEnabled(True)

    @pyqtSlot(QModelIndex)
    def on_tableControl_activated(self, index):
        self.on_tableControl_clicked(index)

    @pyqtSlot()
    def on_btnOff_clicked(self):
        self._instrumentController.rigTurnOff()

    @pyqtSlot(int)
    def on_spinRefLevel_valueChanged(self, value):
        self._instrumentController.refLevel = value
