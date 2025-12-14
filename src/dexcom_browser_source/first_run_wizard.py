from csv import Error
from ctypes import ArgumentError
from typing import override
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFormLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget, QWizard, QWizardPage
from pydexcom import Dexcom
from dexcom_browser_source.config import AppConfig


class FirstRunWizard(QWizard):
    def __init__(self, app_config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("First Run Setup Wizard - Dexcom Browser Source")
        self.resize(720, 480)
        self.setFixedSize(720, 480)
        self.setWizardStyle(QWizard.WizardStyle.ClassicStyle)
        self._app_config: AppConfig = app_config

        _ = self.addPage(IntroductionPage(parent=self))
        _ = self.addPage(LicenseAcceptPage(parent=self))
        _ = self.addPage(DexcomLoginPage(app_config, parent=self))
        _ = self.addPage(DonatePage(parent=self))
        _ = self.addPage(FinishPage(app_config, parent=self))
        self.show()

class IntroductionPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setTitle("First Run Setup Wizard")

        self._layout: QVBoxLayout = QVBoxLayout()
        self._label: QLabel = QLabel()
        self.setup_layout()

    def setup_layout(self):
        self._label = QLabel(
            text="Thank you for using Dexcom Browser Source. " +
            "This first-run wizard will help you configure this program. " +
            "Make sure you've read the README and have Dexcom Share service enabled for your Dexcom account. " +
            "Please press the \"NEXT\" button to continue.",
            wordWrap=True)
        self._layout.addWidget(self._label)
        self.setLayout(self._layout)

class LicenseAcceptPage(QWizardPage):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setTitle("License Agreement")
        self.setSubTitle("Agree to this free and open-source LICENSE AGREEMENT to continue.")

        self._layout: QFormLayout = QFormLayout()
        self._license_text_edit: QTextEdit = QTextEdit()
        self._license_accept_check_box: QCheckBox = QCheckBox()
        self.setup_layout()
        self.registerField("accept.license*", self._license_accept_check_box)

    def setup_layout(self):
        self._license_text_edit = QTextEdit(plainText="""MIT License

Copyright (c) 2025 meatball

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""", readOnly=True)
        self._license_accept_check_box = QCheckBox("I agree to this LICENSE AGREEMENT and wish to continue", self)

        self._layout.addWidget(self._license_text_edit)
        self._layout.addWidget(self._license_accept_check_box)
        self.setLayout(self._layout)

class DexcomLoginPage(QWizardPage):
    def __init__(self, app_config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._app_config: AppConfig = app_config
        self.setTitle("Login to Dexcom Share")
        self.setSubTitle("Please provide your Dexcom Share account information.")

        self._layout: QFormLayout = QFormLayout()
        self._username_line_edit: QLineEdit = QLineEdit()
        self._password_line_edit: QLineEdit = QLineEdit()
        self._login_push_button: QPushButton = QPushButton()
        self._login_status_label: QLabel = QLabel()
        self.setup_layout()
        self.registerField("dexcom.loggedin*", self._login_push_button)

    def setup_layout(self):
        self._password_line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._login_push_button.setText("Login to Dexcom Share")
        self._login_push_button.setCheckable(True)
        _ = self._login_push_button.clicked.connect(self.login)
        self._login_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._layout.addRow(QLabel("Dexcom Username"), self._username_line_edit)
        self._layout.addRow(QLabel("Dexcom Password"), self._password_line_edit)
        self._layout.addRow(self._login_push_button)
        self._layout.addRow(self._login_status_label)
        self.setLayout(self._layout)

    def login(self) -> Dexcom | Exception:
        try:
            dexcom: Dexcom = Dexcom(username=self._username_line_edit.text(), password=self._password_line_edit.text())
            self._login_status_label.setText("Login successful!")
            self._login_status_label.setStyleSheet("QLabel { color: green; }")
            self._login_push_button.setChecked(True)
            self._app_config.config["dexcom"]["username"] = self._username_line_edit.text()
            self._app_config.config["dexcom"]["password"] = self._password_line_edit.text()
            return dexcom
        except Exception as e:
            self._login_status_label.setText(str(e))
            self._login_status_label.setStyleSheet("QLabel { color: red; }")
            return e

class DonatePage(QWizardPage):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setTitle("Do You Want to Donate?")
        self.setSubTitle("Give back to the authors if you want!")

        self._layout: QVBoxLayout = QVBoxLayout()
        self.setup_layout()

    def setup_layout(self):
        self.setLayout(self._layout)

class FinishPage(QWizardPage):
    def __init__(self, app_config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._app_config: AppConfig = app_config
        self.setTitle("First Run Setup Wizard Complete")

        self._layout: QVBoxLayout = QVBoxLayout()
        self.setup_layout()

    def setup_layout(self):
        self.setLayout(self._layout)

    @override
    def validatePage(self, /) -> bool:
        self._app_config.save()
        return super().validatePage()