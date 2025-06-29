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
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar
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
        
