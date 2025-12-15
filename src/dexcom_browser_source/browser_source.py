from typing import override
from waitress.server import BaseWSGIServer, MultiSocketServer
from pydexcom.dexcom import Dexcom
from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from flask import Blueprint, Flask
from flask.views import ft
from waitress.server import create_server

from dexcom_browser_source.config import AppConfig


class WaitressThread(QThread):
    def __init__(self, app_config: AppConfig):
        self._app_config: AppConfig = app_config
        self._waitress_server: MultiSocketServer | BaseWSGIServer = create_server(
            application=create_app(app_config=self._app_config))
        super().__init__()

    @override
    def run(self, /) -> None:
        self._waitress_server.run()

    @override
    def quit(self, /) -> None:
        self._waitress_server.close()
        super().quit()

class BrowserSourceDetailsDialog(QDialog):
    def __init__(self, app: QApplication, app_config: AppConfig, parent: QWidget | None = None):
        self._app: QApplication = app
        self._app_config: AppConfig = app_config
        self._waitress_thread: WaitressThread = WaitressThread(app_config=self._app_config)
        self._layout: QVBoxLayout = QVBoxLayout()
        self._button_layout: QHBoxLayout = QHBoxLayout()
        self._waitress_status_label: QLabel = QLabel()
        self._waitress_start_button: QPushButton = QPushButton("Start Waitress")
        self._waitress_stop_button: QPushButton = QPushButton("Stop Waitress")
        super().__init__(parent)
        self.setWindowTitle("Browser Source Details - Dexcom Browser Source")
        _ = self._waitress_start_button.clicked.connect(self.start_waitress)
        _ = self._waitress_stop_button.clicked.connect(self.stop_waitress)

        self._waitress_status_label.setText("# Waitress is Offline")
        self._waitress_status_label.setStyleSheet("QLabel { color: red; }")
        self._waitress_status_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self._waitress_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._waitress_status_label)
        self._waitress_start_button.setText("Start Waitress")
        self._button_layout.addWidget(self._waitress_start_button)
        self._waitress_stop_button.setEnabled(False)
        self._button_layout.addWidget(self._waitress_stop_button)
        self._layout.addLayout(self._button_layout)
        self.setLayout(self._layout)

        self.start_waitress()


    def start_waitress(self):
        _ = self._waitress_thread.started.connect(self.on_waitress_start)
        _ = self._waitress_thread.finished.connect(self.on_waitress_finish)
        _ = self._app.aboutToQuit.connect(self.stop_waitress)
        self._waitress_thread.start()

    def stop_waitress(self):
        self._waitress_thread.quit()
        _ = self._waitress_thread.wait()
        self._waitress_thread = WaitressThread(app_config=self._app_config)

    def on_waitress_start(self):
        self._waitress_start_button.setText("Restart Waitress")
        self._waitress_stop_button.setEnabled(True)

        self._waitress_status_label.setText("# Waitress is Online")
        self._waitress_status_label.setStyleSheet("QLabel { color: green; }")

    def on_waitress_finish(self):
        self._waitress_start_button.setText("Start Waitress")
        self._waitress_stop_button.setEnabled(False)

        self._waitress_status_label.setText("# Waitress is Offline")
        self._waitress_status_label.setStyleSheet("QLabel { color: red; }")

# flask app for waitress to serve
def create_app(app_config: AppConfig) -> Flask:
    app: Flask = Flask(__name__)

    dexcom: Dexcom = Dexcom(username=str(app_config.config["dexcom"]["username"]),
        password=str(app_config.config["dexcom"]["password"]))

    glucose_blueprint: Blueprint = Blueprint('glucose', import_name=__name__, url_prefix='/glucose')
    def render_glucose_template(path: str) -> ft.ResponseReturnValue:
        return app.send_static_file("glucose.html")
    glucose_blueprint.add_url_rule("/<path:path>", view_func=render_glucose_template)
    glucose_blueprint.add_url_rule("/", view_func=render_glucose_template, defaults={'path': ''})
    app.register_blueprint(blueprint=glucose_blueprint)

    chart_blueprint: Blueprint = Blueprint('chart', import_name=__name__, url_prefix='/chart')
    def render_chart_template(path: str) -> ft.ResponseReturnValue:
        return app.send_static_file("chart.html")
    chart_blueprint.add_url_rule("/<path:path>", view_func=render_chart_template)
    chart_blueprint.add_url_rule("/", view_func=render_chart_template, defaults={'path': ''})
    app.register_blueprint(blueprint=chart_blueprint)
    return app