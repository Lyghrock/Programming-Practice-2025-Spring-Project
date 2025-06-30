AUDIO_ADDRESS = r"D:\Desk_Pet_Data_Storage\Voice_Bank"
DEFINITION_ADDRESS = r"D:\Desk_Pet_Data_Storage\Text_Data\definition.txt"
TRANSLATION_ADDRESS = r"D:\Desk_Pet_Data_Storage\Text_Data\translation.txt"
WORD_BANK_ADDRESS = r"D:\Desk_Pet_Data_Storage\Word_Data\word_bank.db"
WORD_BROCHURE_ADDRESS = r"D:\Desk_Pet_Data_Storage\Word_Data\word_brochure.db"
TEST_RESULT_ADDRESS = r"D:\Desk_Pet_Data_Storage\Test_Data"

INITIAL_ADDRESS = r"D:\Python_Audio_Processing\Word_bank\Initialized_Word_Bank.txt"
TEST_ADDRESS = r"D:\Python_Audio_Processing\Word_bank\Test_Word_Bank.txt"
BLANK_AUDIO_ADDRESS = r"D:\Python_Audio_Processing\default_audio.mp3"

Initial_Word_list = list()

REQUEST_HEADERS = {
    "User-Agent" : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'
}


import time
from PyQt5.QtCore import (
    Qt, QTimer                      
    )
from PyQt5.QtGui import (
    QFont
)
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QProgressBar, QApplication, QComboBox, QMessageBox,
    QSpinBox, QLineEdit, QDialogButtonBox, QFileDialog
)

from PyQt5.uic import loadUi
from UI_File.Reverse_Widget.Progress_Bar import Ui_Progress_Keeper

class ProgressDialog(QDialog, Ui_Progress_Keeper):
    def __init__(self, title = "Loading Initialization Data", parent = None):
        super().__init__(parent)
        
        self.setupUi(self)
        self.setModal(True)

    def update_progress(self, percent,trait):
        self.progress_keeper.setValue(percent)
        self.Annotations.setText(f"Current Progress of {trait}: {percent}%")
        
        
class CustomItemDialog(QDialog):
    def __init__(self, parent, title, label_text, items):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout()

        label = QLabel(label_text)
        label.setWordWrap(True)
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)

        self.combo = QComboBox()
        self.combo.addItems(items)
        self.combo.setMinimumHeight(30)
        self.combo.setFont(QFont("Arial", 12))
        layout.addWidget(self.combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def getValue(self):
        return self.combo.currentText()
    
    @staticmethod
    def getItem(parent, title, label, items):
        dialog = CustomItemDialog(parent, title, label, items)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return dialog.getValue(), True
        else:
            return None, False

        

class CustomIntDialog(QDialog):
    def __init__(self, parent, title, label_text, min_val=0, max_val=100, default = 30):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout()

        label = QLabel(label_text)
        label.setWordWrap(True)
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)

        self.spinbox = QSpinBox()
        self.spinbox.setRange(min_val, max_val)
        self.spinbox.setValue(default)
        self.spinbox.setFont(QFont("Arial", 12))
        self.spinbox.setMinimumHeight(30)
        layout.addWidget(self.spinbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def getValue(self):
        return self.spinbox.value()
    
    @staticmethod
    def getInt(parent, title, label, min_val=0, max_val=100, default = 30):
        dialog = CustomIntDialog(parent, title, label, min_val, max_val, default)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return dialog.getValue(), True
        else:
            return None, False
    


class CustomTextDialog(QDialog):
    def __init__(self, parent, title, label_text):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(400, 250)

        layout = QVBoxLayout()

        label = QLabel(label_text)
        label.setWordWrap(True)
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)

        self.line_edit = QLineEdit()
        self.line_edit.setFont(QFont("Arial", 12))
        self.line_edit.setMinimumHeight(30)
        layout.addWidget(self.line_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def getValue(self):
        return self.line_edit.text()
    
    @staticmethod
    def getText(parent, title, label):
        dialog = CustomTextDialog(parent,title, label)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return dialog.getValue(), True
        else:
            return '', False
    
    
    
class CustomFileOpenDialog(QDialog):
    def __init__(self, parent, title="Open File", label_text="Please choose a file:", file_filter="All Files (*)"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 180)

        self.selected_path = ""

        layout = QVBoxLayout()

        label = QLabel(label_text)
        label.setWordWrap(True)
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)

        self.file_button = QPushButton("Browse...")
        self.file_button.setMinimumHeight(35)
        self.file_button.setFont(QFont("Arial", 11))
        self.file_button.clicked.connect(lambda: self.open_file(file_filter))
        layout.addWidget(self.file_button)

        self.path_label = QLabel("No file selected.")
        self.path_label.setFont(QFont("Arial", 10))
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def open_file(self, file_filter):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if file_path:
            self.selected_path = file_path
            self.path_label.setText(file_path)

    def getPath(self):
        return self.selected_path

    @staticmethod
    def getOpenFileName(parent, title="Open File", label="Please choose a file:", file_filter="All Files (*)"):
        dialog = CustomFileOpenDialog(parent, title, label, file_filter)
        result = dialog.exec_()
        if result == QDialog.Accepted and dialog.getPath():
            return dialog.getPath(), True
        else:
            return "", False


def show_wrapped_message_box(parent, title, message, icon=QMessageBox.Information):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setIcon(icon)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)

    # 设置字体
    font = QFont("Arial", 11)
    msg_box.setFont(font)

    # 让内部 QLabel 自动换行
    label = msg_box.findChild(QLabel)
    if label:
        label.setWordWrap(True)
        label.setFont(font)
        label.setMinimumWidth(400)  # 可调宽度
        label.setMaximumWidth(600)
        
    msg_box.setStyleSheet("""
        QLabel {
            min-width: 400px;
            max-width: 600px;
            font-size: 11pt;
        }
    """)
    
    msg_box.setTextFormat(Qt.PlainText)

    msg_box.exec_()