import sys
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from dexcom_browser_source.about_dialog import AboutDialog
from dexcom_browser_source.browser_source import BrowserSourceDetailsDialog, WaitressStatusDialog, WaitressThread
from dexcom_browser_source.config import AppConfig
from dexcom_browser_source.settings_dialog import SettingsDialog


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent: QObject, app_config: AppConfig):
        if not self.isSystemTrayAvailable():
            _ = QMessageBox.critical(None, "Dexcom Browser Source", "The system tray is unavailable! Dexcom Browser Source will now close!")
            sys.exit(1)
        super().__init__(parent)
        self._waitress_thread: WaitressThread = WaitressThread(app_config)

        self._waitress_status_dialog: WaitressStatusDialog = WaitressStatusDialog(parent=None, waitress_thread=self._waitress_thread)
        self._browser_source_details_dialog: BrowserSourceDetailsDialog = BrowserSourceDetailsDialog(parent=None, waitress_thread=self._waitress_thread)
        self._settings_dialog: SettingsDialog = SettingsDialog(parent=None, app_config=app_config)
        self._about_dialog: AboutDialog = AboutDialog()

        self._waitress_status_action: QAction = QAction()
        self._browser_source_action: QAction = QAction()
        self._settings_action: QAction = QAction()
        self._about_action: QAction = QAction()
        self._quit_action: QAction = QAction()
        self.create_actions()
        self._context_menu: QMenu = self.create_context_menu()
        self.setContextMenu(self._context_menu)
        self._waitress_thread.start()

    def create_actions(self):
        self._waitress_status_action = QAction("Waitress Status", self)
        _ = self._waitress_status_action.triggered.connect(self._waitress_status_dialog.show)
        self._browser_source_action = QAction("Browser Source Details", self)
        _ = self._browser_source_action.triggered.connect(self._browser_source_details_dialog.show)
        self._settings_action = QAction("Settings", self)
        _ = self._settings_action.triggered.connect(self._settings_dialog.show)
        self._about_action = QAction("About", self)
        _ = self._about_action.triggered.connect(self._about_dialog.show)
        self._quit_action = QAction("Quit", self)
        _ = self._quit_action.triggered.connect(QApplication.quit)

    def create_context_menu(self):
        context_menu = QMenu()
        context_menu.addAction(self._waitress_status_action)
        context_menu.addAction(self._browser_source_action)
        context_menu.addAction(self._settings_action)
        context_menu.addAction(self._about_action)
        context_menu.addAction(self._quit_action)
        return context_menu
