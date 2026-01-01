import sys
from PySide6.QtWidgets import QApplication
from dexcom_browser_source.config import AppConfig
from dexcom_browser_source.first_run_wizard import FirstRunWizard
from dexcom_browser_source.system_tray import SystemTrayIcon

app_config: AppConfig = AppConfig()
app: QApplication = QApplication(sys.argv)

system_tray_icon: SystemTrayIcon = SystemTrayIcon(parent=app, app=app, app_config=app_config)
system_tray_icon.show()

if app_config.first_run:
    _ = FirstRunWizard(app=app, app_config=app_config, system_tray_icon=system_tray_icon)

app.setQuitOnLastWindowClosed(False)
sys.exit(app.exec())
