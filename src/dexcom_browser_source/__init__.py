import sys
from PySide6.QtWidgets import QApplication
from dexcom_browser_source.config import AppConfig
from dexcom_browser_source.first_run_wizard import FirstRunWizard
from dexcom_browser_source.system_tray import SystemTrayIcon

app_config: AppConfig = AppConfig()

app: QApplication = QApplication(sys.argv)
_ = app.setStyle('fusion')

systray: SystemTrayIcon = SystemTrayIcon(app)
systray.show()

if app_config.first_run:
    first_run_wizard: FirstRunWizard = FirstRunWizard()
    first_run_wizard.show()

app.setQuitOnLastWindowClosed(False)
sys.exit(app.exec())
