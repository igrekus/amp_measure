from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QRunnable, QThreadPool
from PyQt5.QtWidgets import QWidget, QComboBox, QLabel, QMessageBox, QDoubleSpinBox

from deviceselectwidget import DeviceSelectWidget


class MeasureTask(QRunnable):

    def __init__(self, fn, end, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.end = end
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.fn(*self.args, **self.kwargs)
        self.end()


class MeasureWidget(QWidget):

    selectedChanged = pyqtSignal(str)
    sampleFound = pyqtSignal()
    measureComplete = pyqtSignal()

    def __init__(self, parent=None, controller=None):
        super().__init__(parent=parent)

        self._ui = uic.loadUi('measurewidget.ui', self)
        self._controller = controller
        self._threads = QThreadPool()

        self._devices = DeviceSelectWidget(parent=self, params=self._controller.deviceParams)
        self._ui.layParams.insertWidget(0, self._devices)
        self._devices.selectedChanged.connect(self.on_selectedChanged)

        self._selectedDevice = self._devices.selected

    def check(self):
        print('checking...')
        self._modeDuringCheck()
        self._threads.start(MeasureTask(self._controller.check,
                                        self.checkTaskComplete,
                                        self._selectedDevice))

    def checkTaskComplete(self):
        print('check complete')
        if not self._controller.present:
            print('sample not found')
            # QMessageBox.information(self, 'Ошибка', 'Не удалось найти образец, проверьте подключение')
            self._modePreCheck()
            return

        print('found sample')
        self._modePreMeasure()
        self.sampleFound.emit()

    def measure(self):
        print('measuring...')
        self._modeDuringMeasure()
        self._threads.start(MeasureTask(self._controller.measure,
                                        self.measureTaskComplete,
                                        self._selectedDevice))

    def measureTaskComplete(self):
        print('measure complete')
        # TODO check if measure completed successfully?
        if not self._controller.hasResult:
            print('error during measurement')
            return

        self._modePreCheck()
        self.measureComplete.emit()

    @pyqtSlot()
    def on_instrumentsConnected(self):
        self._modePreCheck()

    @pyqtSlot()
    def on_btnCheck_clicked(self):
        print('checking sample presence')
        self.check()

    @pyqtSlot()
    def on_btnMeasure_clicked(self):
        print('start measure')
        self.measure()

    @pyqtSlot(str)
    def on_selectedChanged(self, value):
        self._selectedDevice = value
        self.selectedChanged.emit(value)

    def _modePreConnect(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._devices.enabled = True

    def _modePreCheck(self):
        self._ui.btnCheck.setEnabled(True)
        self._ui.btnMeasure.setEnabled(False)
        self._devices.enabled = True

    def _modeDuringCheck(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._devices.enabled = False

    def _modePreMeasure(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(True)
        self._devices.enabled = False

    def _modeDuringMeasure(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._devices.enabled = False


class MeasureWidgetWithSecondaryParameters(MeasureWidget):
    secondaryChanged = pyqtSignal(dict)

    def __init__(self, parent=None, controller=None):
        super().__init__(parent=parent, controller=controller)

        self._params = 0

        # self._spinFreq = QDoubleSpinBox(parent=self)
        # self._spinFreq.setMinimum(0)
        # self._spinFreq.setMaximum(20_000)
        # self._spinFreq.setSingleStep(1)
        # self._devices._layout.addRow('F=', self._spinFreq)   # 0 .. 20k

        self._spinDeltaFreq = QDoubleSpinBox(parent=self)
        self._spinDeltaFreq.setMinimum(0)
        self._spinDeltaFreq.setMaximum(100)
        self._spinDeltaFreq.setSingleStep(1)
        self._spinDeltaFreq.setValue(0.1)
        self._devices._layout.addRow('ΔF=', self._spinDeltaFreq)   # 0..100, 1

        self._spinPmin = QDoubleSpinBox(parent=self)
        self._spinPmin.setMinimum(-30)
        self._spinPmin.setMaximum(20)
        self._spinPmin.setSingleStep(0.1)
        self._spinPmin.setValue(10.0)
        self._devices._layout.addRow('Pmin=', self._spinPmin)   # -30 ... 20

        self._spinPmax = QDoubleSpinBox(parent=self)
        self._spinPmax.setMinimum(-30)
        self._spinPmax.setMaximum(20)
        self._spinPmax.setSingleStep(0.1)
        self._spinPmax.setValue(20.0)
        self._devices._layout.addRow('Pmax=', self._spinPmax)   # -30 .. 20, 0.1

        self._spinDeltaP1 = QDoubleSpinBox(parent=self)
        self._spinDeltaP1.setMinimum(-5)
        self._spinDeltaP1.setMaximum(10)
        self._spinDeltaP1.setSingleStep(0.01)
        self._spinDeltaP1.setValue(1.0)
        self._devices._layout.addRow('ΔP1=', self._spinDeltaP1)   # -5 .. 10

        self._spinDeltaP2 = QDoubleSpinBox(parent=self)
        self._spinDeltaP2.setMinimum(-4)
        self._spinDeltaP2.setMaximum(10)
        self._spinDeltaP2.setSingleStep(0.01)
        self._spinDeltaP2.setValue(1.0)
        self._devices._layout.addRow('ΔP2=', self._spinDeltaP2)   # -5 .. 10, step .01

        self._connectSignals()

    def _connectSignals(self):
        # self._spinFreq.valueChanged.connect(self.on_params_changed)
        self._spinDeltaFreq.valueChanged.connect(self.on_params_changed)
        self._spinPmin.valueChanged.connect(self.on_params_changed)
        self._spinPmax.valueChanged.connect(self.on_params_changed)
        self._spinDeltaP1.valueChanged.connect(self.on_params_changed)
        self._spinDeltaP2.valueChanged.connect(self.on_params_changed)

    def _modePreConnect(self):
        super()._modePreConnect()
        # self._spinFreq.setEnabled(True)

    def _modePreCheck(self):
        super()._modePreCheck()
        # self._spinFreq.setEnabled(True)

    def _modeDuringCheck(self):
        super()._modeDuringCheck()
        # self._spinFreq.setEnabled(False)

    def _modePreMeasure(self):
        super()._modePreMeasure()
        # self._spinFreq.setEnabled(False)

    def _modeDuringMeasure(self):
        super()._modeDuringMeasure()
        # self._spinFreq.setEnabled(False)

    def check(self):
        print('subclass checking...')
        self._modeDuringCheck()
        self._threads.start(MeasureTask(self._controller.check,
                                        self.checkTaskComplete,
                                        [self._selectedDevice, self._params]))

    def measure(self):
        print('subclass measuring...')
        self._modeDuringMeasure()
        self._threads.start(MeasureTask(self._controller.measure,
                                        self.measureTaskComplete,
                                        [self._selectedDevice, self._params]))

    def on_params_changed(self, value):
        params = {
            # 'F': self._spinFreq.value(),
            'dF': self._spinDeltaFreq.value(),
            'Pmin': self._spinPmin.value(),
            'Pmax': self._spinPmax.value(),
            'dP1': self._spinDeltaP1.value(),
            'dP2': self._spinDeltaP2.value()
        }
        self.secondaryChanged.emit(params)
