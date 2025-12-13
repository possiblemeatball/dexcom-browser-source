import sys
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from dexcom_browser_source.about_dialog import AboutDialog
from dexcom_browser_source.settings_window import SettingsWindow


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent: QObject):
        if not self.isSystemTrayAvailable():
            _ = QMessageBox.critical(None, "Dexcom Browser Source", "The system tray is unavailable! Dexcom Browser Source will now close!")
            sys.exit(1)
        super().__init__(parent)

        self._settings_action: QAction = QAction()
        self._about_action: QAction = QAction()
        self._quit_action: QAction = QAction()
        self.create_actions()

        self._context_menu: QMenu = self.create_context_menu()
        self.setContextMenu(self._context_menu)

    def create_actions(self):
        self._settings_action = QAction("Settings", self)
        _ = self._settings_action.triggered.connect(SettingsWindow().show)
        self._about_action = QAction("About", self)
        _ = self._about_action.triggered.connect(AboutDialog().show)
        self._quit_action = QAction("Quit", self)
        _ = self._quit_action.triggered.connect(QApplication.quit)

    def create_context_menu(self):
        context_menu = QMenu()
        context_menu.addAction(self._settings_action)
        context_menu.addAction(self._about_action)
        context_menu.addAction(self._quit_action)
        return context_menu
