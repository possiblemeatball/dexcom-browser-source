import base64
from datetime import datetime
from flask import Blueprint, Flask
from io import BytesIO
from typing import override
from matplotlib.axes import Subplot
from waitress.server import create_server
from waitress.server import BaseWSGIServer, MultiSocketServer
from pydexcom.dexcom import Dexcom
from pydexcom.glucose_reading import GlucoseReading
from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
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
        _ = self._app.aboutToQuit.connect(self.stop_waitress)
        _ = self._waitress_thread.started.connect(self.on_waitress_start)
        _ = self._waitress_thread.finished.connect(self.on_waitress_finish)
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
            username=str(app_config.config['dexcom']['account']['username']),
            password=str(app_config.config['dexcom']['account']['password'])
        )

        self.add_url_rule(rule='/current/trend_arrow', view_func=self.serve_current_glucose_reading_trend_arrow)
        self.add_url_rule(rule='/current/mg_dl', view_func=self.serve_current_glucose_reading_mg_dl)
        self.add_url_rule(rule='/current/mmol_l', view_func=self.serve_current_glucose_reading_mmol_l)
        self.add_url_rule(rule='/current', view_func=self.serve_current_glucose_reading)
        self.add_url_rule(rule='/last/<int:hours>', view_func=self.serve_last_readings_graph)
        self.add_url_rule(rule='/last', view_func=self.serve_last_readings_graph, defaults={"hours": self._app_config.config['graph']['last_hours']})

    def serve_current_glucose_reading(self) -> ft.ResponseReturnValue:
        if self._app_config.config['app']['metric']:
            return self.serve_current_glucose_reading_mmol_l()
        else:
            return self.serve_current_glucose_reading_mg_dl()

    def serve_current_glucose_reading_mg_dl(self) -> ft.ResponseReturnValue:
        glucose_reading: GlucoseReading | None = self._dexcom.get_current_glucose_reading()
        if glucose_reading is None:
            return '--', 404
        return f'<span hx-get="/api/current" hx-trigger="load delay:1m" hx-swap="outerHTML">{glucose_reading.mg_dl}</span>', 200

    def serve_current_glucose_reading_mmol_l(self) -> ft.ResponseReturnValue:
        glucose_reading: GlucoseReading | None = self._dexcom.get_current_glucose_reading()
        if glucose_reading is None:
            return '--', 404
        return f'<span hx-get="/api/current" hx-trigger="load delay:1m" hx-swap="outerHTML">{glucose_reading.mmol_l}</span>', 200

    def serve_current_glucose_reading_trend_arrow(self) -> ft.ResponseReturnValue:
        glucose_reading: GlucoseReading | None = self._dexcom.get_current_glucose_reading()
        if glucose_reading is None:
            return '--', 404
        return f'<span hx-get="/api/current/trend_arrow" hx-trigger="load delay:1m" hx-swap="outerHTML">{glucose_reading.trend_arrow}</span>', 200

    def serve_last_readings_graph(self, hours: int) -> ft.ResponseReturnValue:
        metric: bool = bool(self._app_config.config['app']['metric'])
        hyperglycemia: float | int = self._app_config.config['dexcom']['hyperglycemia_level']
        hypoglycemia: float | int = self._app_config.config['dexcom']['hypoglycemia_level']
        ybound_up: float | int = self._app_config.config['graph']['height_limit']
        ybound_low: float | int = 3.9 if metric else 40
        tick_color: str = "white" if self._app_config.config['graph']['colors']['appearance'] == "dark" else "black"
        glucose_readings: list[GlucoseReading] = self._dexcom.get_glucose_readings(minutes=(60 * hours))

        chart_figure: Figure = Figure()
        chart_axis: Subplot = chart_figure.subplots()

        x: list[datetime] = []
        y: list[float | int] = []
        for reading in glucose_readings:
            glucose: float | int = reading.mmol_l if metric else reading.mg_dl
            time: datetime = reading.datetime
            x.append(time)
            y.append(glucose)
        x.reverse()
        y.reverse()

        _ = chart_axis.spines['top'].set_visible(False)
        _ = chart_axis.spines['right'].set_visible(False)
        _ = chart_axis.spines['bottom'].set_visible(False)
        _ = chart_axis.spines['left'].set_visible(False)
        _ = chart_axis.xaxis.set_major_locator(locator=HourLocator(byhour=range(0, 25, round(hours / 4))))
        _ = chart_axis.xaxis.set_major_formatter(formatter=DateFormatter(fmt='%I %p', tz=x[0].tzinfo))
        _ = chart_axis.yaxis.set_ticks(ticks=[ybound_low, hypoglycemia, hyperglycemia, ybound_up])
        _ = chart_axis.set_xlim(left=x[0], right=x[-1])
        _ = chart_axis.yaxis.set_ticks_position('right')
        _ = chart_axis.set_ybound(lower=ybound_low, upper=ybound_up)
        _ = chart_axis.set_autoscaley_on(False)
        _ = chart_axis.axhspan(ymin=(hypoglycemia + 4), ymax=(hyperglycemia - 4), facecolor=self._app_config.config['graph']['colors']['normal'], alpha=0.25)
        _ = chart_axis.axhspan(ymin=hyperglycemia, ymax=ybound_up, facecolor=self._app_config.config['graph']['colors']['hyperglycemia'], alpha=0.5)
        _ = chart_axis.axhspan(ymin=ybound_low, ymax=hypoglycemia, facecolor=self._app_config.config['graph']['colors']['hypoglycemia'], alpha=0.5)
        _ = chart_axis.tick_params(colors=tick_color)
        _ = chart_axis.plot(x, y, color=tick_color, marker='o', markersize=2, linewidth=0)

        chart_buffer: BytesIO = BytesIO()
        chart_figure.savefig(fname=chart_buffer, format="png", transparent=True)
        data: str = base64.b64encode(chart_buffer.getbuffer()).decode("ascii")
        chart_buffer.close()
        return f'<img src="data:image/png;base64,{data}" hx-get="/api/last" hx-trigger="load delay:1m" hx-swap="outerHTML" />', 200

class StaticBlueprint(Blueprint):
    def __init__(self, name: str, url_prefix: str, app: Flask, app_config: AppConfig) -> None:
        super().__init__(name=name, import_name=__name__, url_prefix=url_prefix)
        self._app: Flask = app
        self._app_config: AppConfig = app_config

        self.add_url_rule(rule="/<path:_path>", view_func=self.serve_static_html)
        self.add_url_rule(rule="", view_func=self.serve_static_html, defaults={'_path': ''})

    def serve_static_html(self, _path: str) -> ft.ResponseReturnValue:
        return self._app.send_static_file(filename=f'{self.name}.html')

# flask app for waitress to serve
def create_app(app_config: AppConfig) -> Flask:
    app: Flask = Flask(__name__)

    dexcom_api_blueprint: DexcomAPIBlueprint = DexcomAPIBlueprint(app_config=app_config)
    glucose_blueprint: StaticBlueprint = StaticBlueprint(app=app, app_config=app_config, name='glucose', url_prefix='/glucose')
    chart_blueprint: StaticBlueprint = StaticBlueprint(app=app, app_config=app_config, name='chart', url_prefix='/chart')
    app.register_blueprint(blueprint=dexcom_api_blueprint)
    app.register_blueprint(blueprint=glucose_blueprint)
    app.register_blueprint(blueprint=chart_blueprint)
    return app