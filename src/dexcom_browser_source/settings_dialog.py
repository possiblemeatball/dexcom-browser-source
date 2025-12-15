from PySide6.QtWidgets import QDialog, QWidget


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.resize(720, 480)
        self.setFixedSize(720, 480)
        self.setWindowTitle("Dexcom Browser Source - Settings")