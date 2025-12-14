import sys
from PySide6.QtWidgets import QApplication
import qdarktheme
from dexcom_browser_source.config import AppConfig
from dexcom_browser_source.first_run_wizard import FirstRunWizard
from dexcom_browser_source.system_tray import SystemTrayIcon

app_config: AppConfig = AppConfig()
app: QApplication = QApplication(sys.argv)
app.setStyleSheet(qdarktheme.load_stylesheet(theme=str(app_config.config["app"]["appearance"])))

systray: SystemTrayIcon = SystemTrayIcon(app)
systray.show()

if app_config.first_run:
    first_run_wizard: FirstRunWizard = FirstRunWizard(app_config)

app.setQuitOnLastWindowClosed(False)
sys.exit(app.exec())
