from PySide6.QtWidgets import QApplication, QDialog, QWidget

from dexcom_browser_source.config import AppConfig


class SettingsDialog(QDialog):
    def __init__(self, app: QApplication, app_config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._app: QApplication = app
        self._app_config: AppConfig = app_config

        self.resize(720, 480)
        self.setFixedSize(720, 480)
        self.setWindowTitle("Dexcom Browser Source - Settings")