import sys
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from dexcom_browser_source.about_dialog import AboutDialog
from dexcom_browser_source.browser_source import BrowserSourceDetailsDialog
from dexcom_browser_source.config import AppConfig
from dexcom_browser_source.settings_dialog import SettingsDialog


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent: QObject, app_config: AppConfig):
        if not self.isSystemTrayAvailable():
            _ = QMessageBox.critical(None, "Dexcom Browser Source", "The system tray is unavailable! Dexcom Browser Source will now close!")
            sys.exit(1)

        self.browser_source_details_dialog: BrowserSourceDetailsDialog = BrowserSourceDetailsDialog(parent=None, app_config=app_config)
        self.settings_dialog: SettingsDialog = SettingsDialog(parent=None, app_config=app_config)
        self.about_dialog: AboutDialog = AboutDialog()
        self._browser_source_action: QAction = QAction()
        self._settings_action: QAction = QAction()
        self._about_action: QAction = QAction()
        self._quit_action: QAction = QAction()
        super().__init__(parent)

        self._context_menu: QMenu = self.create_context_menu()
        self.setContextMenu(self._context_menu)

    def create_context_menu(self):
        self._browser_source_action = QAction("Browser Source Details", self)
        self._settings_action = QAction("Settings", self)
        self._about_action = QAction("About", self)
        self._quit_action = QAction("Quit", self)
        _ = self._browser_source_action.triggered.connect(self.browser_source_details_dialog.show)
        _ = self._settings_action.triggered.connect(self.settings_dialog.show)
        _ = self._about_action.triggered.connect(self.about_dialog.show)
        _ = self._quit_action.triggered.connect(QApplication.quit)

        context_menu = QMenu()
        context_menu.addAction(self._browser_source_action)
        context_menu.addAction(self._settings_action)
        context_menu.addAction(self._about_action)
        context_menu.addAction(self._quit_action)
        return context_menu
