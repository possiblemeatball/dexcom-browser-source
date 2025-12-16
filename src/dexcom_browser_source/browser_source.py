from typing import override
from waitress.server import create_server
from waitress.server import BaseWSGIServer, MultiSocketServer
from pydexcom.dexcom import Dexcom
from pydexcom.glucose_reading import GlucoseReading
from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from flask import Blueprint, Flask
from flask.views import ft

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
        self._button_layout.addWidget(self._waitress_start_button)
        self._waitress_stop_button.setEnabled(False)
        self._button_layout.addWidget(self._waitress_stop_button)
        self._layout.addLayout(self._button_layout)
        self.setLayout(self._layout)

        self.start_waitress()


    def start_waitress(self):
        if self._waitress_thread.isFinished():
            self._waitress_thread = WaitressThread(app_config=self._app_config)
        _ = self._waitress_thread.started.connect(self.on_waitress_start)
        _ = self._waitress_thread.finished.connect(self.on_waitress_finish)
        _ = self._app.aboutToQuit.connect(self.stop_waitress)
        self._waitress_thread.start()

    def stop_waitress(self):
        self._waitress_thread.quit()
        _ = self._waitress_thread.wait()

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

class DexcomAPIBlueprint(Blueprint):
    def __init__(self, dexcom: Dexcom) -> None:
        super().__init__(name="dexcomapi", import_name=__name__, url_prefix='/api')
        self._dexcom: Dexcom = dexcom
        self.add_url_rule(rule='/current', view_func=self.serve_current_glucose_reading)
        self.add_url_rule(rule='/current/mmol_l', view_func=self.serve_current_glucose_reading_mmol_l)
        self.add_url_rule(rule='/current/trend', view_func=self.serve_current_glucose_reading_trend)
        self.add_url_rule(rule='/current/trend/arrow', view_func=self.serve_current_glucose_reading_trend_arrow)
        self.add_url_rule(rule='/current/trend/description', view_func=self.serve_current_glucose_reading_trend_description)
        self.add_url_rule(rule='/last/<int:minutes>', view_func=self.serve_last_readings)
        self.add_url_rule(rule='/last', view_func=self.serve_last_readings, defaults={"minutes": 1440})
        self.add_url_rule(rule='/', view_func=self.serve_error)

    def serve_current_glucose_reading(self) -> ft.ResponseReturnValue:
        glucose_reading: GlucoseReading | None = self._dexcom.get_current_glucose_reading()
        if glucose_reading is None:
            return '--', 404
        return f'{glucose_reading.mg_dl}', 200

    def serve_current_glucose_reading_mmol_l(self) -> ft.ResponseReturnValue:
        glucose_reading: GlucoseReading | None = self._dexcom.get_current_glucose_reading()
        if glucose_reading is None:
            return '--', 404
        return f'{glucose_reading.mmol_l}', 200

    def serve_current_glucose_reading_trend(self) -> ft.ResponseReturnValue:
        glucose_reading: GlucoseReading | None = self._dexcom.get_current_glucose_reading()
        if glucose_reading is None:
            return '--', 404
        return f'{glucose_reading.trend}', 200

    def serve_current_glucose_reading_trend_arrow(self) -> ft.ResponseReturnValue:
        glucose_reading: GlucoseReading | None = self._dexcom.get_current_glucose_reading()
        if glucose_reading is None:
            return '--', 404
        return f'{glucose_reading.trend_arrow}', 200

    def serve_current_glucose_reading_trend_description(self) -> ft.ResponseReturnValue:
        glucose_reading: GlucoseReading | None = self._dexcom.get_current_glucose_reading()
        if glucose_reading is None:
            return '--', 404
        return f'{glucose_reading.trend_description}', 200

    def serve_current_glucose_reading_trend_direction(self) -> ft.ResponseReturnValue:
        glucose_reading: GlucoseReading | None = self._dexcom.get_current_glucose_reading()
        if glucose_reading is None:
            return '--', 404
        return f'{glucose_reading.trend_direction}', 200

    def serve_last_readings(self, minutes: int) -> ft.ResponseReturnValue:
        glucose_readings: list[GlucoseReading] = self._dexcom.get_glucose_readings(minutes=minutes)

        response: str = "<table><tr><th>Date</th><th>Glucose</th><th>Trend Arrow</th></tr>"
        for reading in glucose_readings:
            response = response + f'<tr><td>{reading.datetime}</td><td>{reading.mg_dl} mg/dL</td><td>{reading.trend_arrow}</td></tr>'
        response = response + "</table>"
        return response, 200

    def serve_error(self) -> ft.ResponseReturnValue:
        return '', 403

# flask app for waitress to serve
def create_app(app_config: AppConfig) -> Flask:
    app: Flask = Flask(__name__)

    dexcom: Dexcom = Dexcom(username=str(app_config.config["dexcom"]["username"]),
        password=str(app_config.config["dexcom"]["password"]))
    dexcom_api_blueprint: DexcomAPIBlueprint = DexcomAPIBlueprint(dexcom=dexcom)
    app.register_blueprint(blueprint=dexcom_api_blueprint)

    glucose_blueprint: Blueprint = Blueprint('glucose', import_name=__name__, url_prefix='/glucose')
    def serve_glucose(_path: str) -> ft.ResponseReturnValue:
        return app.send_static_file("glucose.html")
    glucose_blueprint.add_url_rule("/<path:_path>", view_func=serve_glucose)
    glucose_blueprint.add_url_rule("", view_func=serve_glucose, defaults={'_path': ''})
    app.register_blueprint(blueprint=glucose_blueprint)

    chart_blueprint: Blueprint = Blueprint('chart', import_name=__name__, url_prefix='/chart')
    def serve_chart(_path: str) -> ft.ResponseReturnValue:
        return app.send_static_file("chart.html")
    chart_blueprint.add_url_rule("/<path:_path>", view_func=serve_chart)
    chart_blueprint.add_url_rule("", view_func=serve_chart, defaults={'_path': ''})
    app.register_blueprint(blueprint=chart_blueprint)
    return app