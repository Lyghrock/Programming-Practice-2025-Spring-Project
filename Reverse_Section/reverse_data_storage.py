AUDIO_ADDRESS = r"D:\Desk_Pet_Data_Storage\Voice_Bank"
DEFINITION_ADDRESS = r"D:\Desk_Pet_Data_Storage\Text_Data\definition.txt"
TRANSLATION_ADDRESS = r"D:\Desk_Pet_Data_Storage\Text_Data\translation.txt"
INITIAL_ADDRESS = r"D:\Python_Audio_Processing\Word_bank\Initialized_Word_Bank.txt"
TEST_ADDRESS = r"D:\Python_Audio_Processing\Word_bank\Test_Word_Bank.txt"
WORD_BANK_ADDRESS = r"D:\Desk_Pet_Data_Storage\Word_Data\word_bank.db"
BLANK_AUDIO_ADDRESS = r"D:\Python_Audio_Processing\default_audio.mp3"

Initial_Word_list = list()

REQUEST_HEADERS = {
    "User-Agent" : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'
}

from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi

class ProgressDialog(QDialog):
    def __init__(self, title="加载中...", parent=None):
        super().__init__(parent)
        
        # loadUi("", self)
        self.setModal(True)
        
        # self.layout = QVBoxLayout()
        # self.label = QLabel("请稍等，正在初始化…")
        # self.progress_bar = QProgressBar()
        # self.progress_bar.setRange(0, 100)

        # self.layout.addWidget(self.label)
        # self.layout.addWidget(self.progress_bar)
        # self.setLayout(self.layout)

        # self.resize(300, 100)

    def update_progress(self, percent,trait):
        self.progress_bar.setValue(percent)
        self.label.setText(f"Current Progress of {trait}: {percent}%")