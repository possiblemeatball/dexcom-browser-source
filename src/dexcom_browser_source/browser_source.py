from typing import override
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QDialog, QWidget
from flask import Blueprint, Flask
from waitress import serve

from dexcom_browser_source.config import AppConfig


class WaitressThread(QThread):
    def __init__(self, app_config: AppConfig):
        super().__init__()
        self._app_config: AppConfig = app_config

    @override
    def run(self, /) -> None:
        serve(app=create_app(self._app_config))

class WaitressStatusDialog(QDialog):
    def __init__(self, waitress_thread: WaitressThread, parent: QWidget | None = None):
        super().__init__(parent)
        self._waitress_thread: WaitressThread = waitress_thread
        self.setWindowTitle("Waitress Status - Dexcom Browser Source")

class BrowserSourceDetailsDialog(QDialog):
    def __init__(self, waitress_thread: WaitressThread, parent: QWidget | None = None):
        super().__init__(parent)
        self._waitress_thread: WaitressThread = waitress_thread
        self.setWindowTitle("Browser Source Details - Dexcom Browser Source")

# flask app for waitress to serve
def create_app(app_config: AppConfig) -> Flask:
    app: Flask = Flask(__name__)
    glucose_blueprint: Blueprint = Blueprint('glucose', import_name=__name__, url_prefix='/glucose')
    glucose_blueprint.add_url_rule(rule='/')
    chart_blueprint: Blueprint = Blueprint('chart', import_name=__name__, url_prefix='/chart')
    chart_blueprint.add_url_rule(rule='/')

    app.register_blueprint(blueprint=glucose_blueprint)
    app.register_blueprint(blueprint=chart_blueprint)
    return app