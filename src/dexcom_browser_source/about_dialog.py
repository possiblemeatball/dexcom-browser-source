from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from dexcom_browser_source.config import AppConfig


class AboutDialog(QDialog):
    def __init__(self, app: QApplication, app_config: AppConfig, parent: QWidget | None = None):
        self._app: QApplication = app
        self._app_config: AppConfig = app_config
        super().__init__(parent)
        self._layout: QVBoxLayout = QVBoxLayout()
        self._app_label_layout: QHBoxLayout = QHBoxLayout()
        self._app_icon: QIcon = QIcon("assets/icon.svg")
        self._app_icon_label: QLabel = QLabel()
        self._app_label: QLabel = QLabel(f"# {self._app.applicationDisplayName()} v{self._app.applicationVersion()}")

        self._app_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self._app_icon_label.setPixmap(self._app_icon.pixmap(32))
        self._app_label_layout.addWidget(self._app_icon_label)
        self._app_label_layout.addWidget(self._app_label)
        self._layout.addLayout(self._app_label_layout)

        self.resize(self.minimumSize())
        self.setFixedSize(self.minimumSize())
        self.setWindowTitle("About Dexcom Browser Source")
        self.setLayout(self._layout)