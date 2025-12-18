import base64
from datetime import datetime
from io import BytesIO
from typing import override
from matplotlib.axes import Subplot
from waitress.server import create_server
from waitress.server import BaseWSGIServer, MultiSocketServer
from pydexcom.dexcom import Dexcom
from pydexcom.glucose_reading import GlucoseReading
from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from flask import Blueprint, Flask
from flask.views import ft
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter, HourLocator

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
    def __init__(self, app_config: AppConfig) -> None:
        super().__init__(name="dexcomapi", import_name=__name__, url_prefix='/api')
        self._app_config: AppConfig = app_config
        self._dexcom: Dexcom = Dexcom(
            username=str(app_config.config["dexcom"]["username"]),
            password=str(app_config.config["dexcom"]["password"])
        )
        self._metric: bool = bool(app_config.config["dexcom"]["metric"])
        self._hypoglycemia_level: int = int(app_config.config["dexcom"]["hypoglycemia_level"])
        self._hyperglycemia_level: int = int(app_config.config["dexcom"]["hyperglycemia_level"])
        self._graph_limit: int = int(app_config.config["dexcom"]["graph_limit"])

        self.add_url_rule(rule='/current', view_func=self.serve_current_glucose_reading)
        self.add_url_rule(rule='/current/mmol_l', view_func=self.serve_current_glucose_reading_mmol_l)
        self.add_url_rule(rule='/current/trend', view_func=self.serve_current_glucose_reading_trend)
        self.add_url_rule(rule='/current/trend/arrow', view_func=self.serve_current_glucose_reading_trend_arrow)
        self.add_url_rule(rule='/current/trend/description', view_func=self.serve_current_glucose_reading_trend_description)
        self.add_url_rule(rule='/last/<int:hours>/graph', view_func=self.serve_last_readings_as_graph)
        self.add_url_rule(rule='/last/<int:hours>', view_func=self.serve_last_readings)
        self.add_url_rule(rule='/last/graph', view_func=self.serve_last_readings_as_graph, defaults={"hours": 24})
        self.add_url_rule(rule='/last', view_func=self.serve_last_readings, defaults={"hours": 24})
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

    def serve_last_readings(self, hours: int) -> ft.ResponseReturnValue:
        glucose_readings: list[GlucoseReading] = self._dexcom.get_glucose_readings(minutes=(60 * hours))

        response: str = "<table><tr><th>Date</th><th>Glucose</th><th>Trend Arrow</th></tr>"
        for reading in glucose_readings:
            response = response + f'<tr><td>{reading.datetime}</td><td>{reading.mg_dl} mg/dL</td><td>{reading.trend_arrow}</td></tr>'
        response = response + "</table>"
        return response, 200

    def serve_last_readings_as_graph(self, hours: int) -> ft.ResponseReturnValue:
        glucose_readings: list[GlucoseReading] = self._dexcom.get_glucose_readings(minutes=(60 * hours))

        chart_figure: Figure = Figure()
        chart_axis: Subplot = chart_figure.subplots()

        x: list[datetime] = []
        y: list[int] = []
        for reading in glucose_readings:
            mg_dl: int = reading.mg_dl
            time: datetime = reading.datetime
            x.append(time)
            y.append(mg_dl)
        x.reverse()

        _ = chart_axis.spines['top'].set_visible(False)
        _ = chart_axis.spines['right'].set_visible(False)
        _ = chart_axis.spines['bottom'].set_visible(False)
        _ = chart_axis.spines['left'].set_visible(False)
        _ = chart_axis.xaxis.set_major_locator(HourLocator(byhour=range(0, 25, round(hours / 4))))
        _ = chart_axis.xaxis.set_major_formatter(formatter=DateFormatter(fmt='%I %p'))
        _ = chart_axis.yaxis.set_ticks(ticks=[40, self._hypoglycemia_level, self._hyperglycemia_level, self._graph_limit])
        _ = chart_axis.set_xlim(left=x[0], right=x[-1])
        _ = chart_axis.yaxis.set_ticks_position('right')
        _ = chart_axis.yaxis.set_label_position('right')
        _ = chart_axis.set_ybound(lower=40, upper=400)
        _ = chart_axis.set_autoscaley_on(False)
        _ = chart_axis.axhspan(ymin=(self._hypoglycemia_level + 4), ymax=(self._hyperglycemia_level - 4), facecolor='grey', alpha=0.25)
        _ = chart_axis.axhspan(ymin=self._hyperglycemia_level, ymax=self._graph_limit, facecolor='yellow', alpha=0.5)
        _ = chart_axis.axhspan(ymin=40, ymax=self._hypoglycemia_level, facecolor='red', alpha=0.5)
        _ = chart_axis.tick_params(colors=("white" if self._app_config.config["app"]["appearance"] == "dark" else "black"))
        _ = chart_axis.plot(x, y, color=("white" if self._app_config.config["app"]["appearance"] == "dark" else "black"), marker='o', markersize=2, linewidth=0)

        chart_buffer: BytesIO = BytesIO()
        chart_figure.savefig(fname=chart_buffer, format="png", transparent=True)

        data: str = base64.b64encode(chart_buffer.getbuffer()).decode("ascii")
        return f"<img src='data:image/png;base64,{data}' />", 200

    def serve_error(self) -> ft.ResponseReturnValue:
        return '', 403

# flask app for waitress to serve
def create_app(app_config: AppConfig) -> Flask:
    app: Flask = Flask(__name__)

    dexcom_api_blueprint: DexcomAPIBlueprint = DexcomAPIBlueprint(app_config=app_config)
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