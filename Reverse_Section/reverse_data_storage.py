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


import time
from PyQt5.QtCore import QTimer
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
        

class ProgressUpdateTimer:
    def __init__(self, update_callback, interval_ms = 1000):
        """
        :param update_callback: 每次触发UI更新时调用，参数为最新进度数据和耗时（秒）
        :param interval_ms: UI更新的固定间隔（毫秒）
        """
        self.update_callback = update_callback
        self.interval_ms = interval_ms
        
        self._last_update_time = 0  # 上次更新时间戳（秒）
        self._start_time = time.time()  # 计时开始时间
        self._timer = QTimer()
        self._timer.setInterval(self.interval_ms)
        self._timer.timeout.connect(self._on_timeout)
        self._timer.start()
        
        self._latest_progress = None  # 保存最新进度数据，等待下一次刷新
        
    def _on_timeout(self):
        """定时器触发，调用UI更新"""
        if self._latest_progress is not None:
            elapsed = time.time() - self._start_time
            self.update_callback(self._latest_progress, elapsed)
            self._latest_progress = None  # 重置等待刷新数据
            
    def update_progress(self, progress_data):
        """
        任务调用接口，提交最新进度数据
        :param progress_data: dict，例如 {"done": 10, "total": 100}
        """
        self._latest_progress = progress_data
        # 这里不直接刷新，交给定时器下一次触发处理
