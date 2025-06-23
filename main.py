import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QPoint
from UI_File.floating_window_ui import Ui_FloatingWindow      #UI_File表示从那个文件夹里import
from UI_File.antonym_learning_ui import Ui_AntonymLearning
from UI_File.screen_translate_ui import Ui_ScreenTranslate
from UI_File.chat_window_ui import Ui_ChatWindow

class FloatingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_FloatingWindow()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 连接按钮信号
        self.ui.btn_antonym.clicked.connect(self.open_antonym_learning)
        self.ui.btn_translate.clicked.connect(self.open_screen_translate)
        self.ui.btn_deepseek_chat.clicked.connect(lambda: self.open_chat("DeepSeek"))
        self.ui.btn_spray_chat.clicked.connect(lambda: self.open_chat("小喷子"))
        
        # 窗口位置和大小
        self.setGeometry(100, 100, 300, 60)
        
        # 用于拖动窗口
        self.dragging = False
        self.offset = QPoint()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
        
    def open_antonym_learning(self):
        self.hide()
        self.antonym_window = AntonymLearningWindow(self)
        self.antonym_window.show()
        
    def open_screen_translate(self):
        self.hide()
        self.translate_window = ScreenTranslateWindow(self)
        self.translate_window.show()
        
    def open_chat(self, chat_type):
        self.hide()
        self.chat_window = ChatWindow(chat_type, self)
        self.chat_window.show()

class AntonymLearningWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AntonymLearning()
        self.ui.setupUi(self)
        self.parent_window = parent
        
        # 连接按钮信号
        self.ui.btn_submit.clicked.connect(self.submit_answer)
        self.ui.btn_add_word.clicked.connect(self.add_to_vocabulary)
        self.ui.btn_back.clicked.connect(self.close)
        
    def closeEvent(self, event):
        self.parent_window.show()
        event.accept()
        
    # 预留接口
    def submit_answer(self):
        """提交答案接口"""
        pass
        
    def add_to_vocabulary(self):
        """添加到单词本接口"""
        pass

class ScreenTranslateWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ScreenTranslate()
        self.ui.setupUi(self)
        self.parent_window = parent
        
        # 连接按钮信号
        self.ui.btn_select_area.clicked.connect(self.select_area)
        self.ui.btn_translate.clicked.connect(self.translate_text)
        self.ui.btn_back.clicked.connect(self.close)
        
    def closeEvent(self, event):
        self.parent_window.show()
        event.accept()
        
    # 预留接口
    def select_area(self):
        """选择屏幕区域接口"""
        pass
        
    def translate_text(self):
        """翻译文本接口"""
        pass

class ChatWindow(QWidget):
    def __init__(self, chat_type, parent=None):
        super().__init__(parent)
        self.ui = Ui_ChatWindow()
        self.ui.setupUi(self)
        self.parent_window = parent
        self.chat_type = chat_type
        
        # 设置窗口标题
        self.setWindowTitle(f"聊天 - {chat_type}")
        
        # 连接按钮信号
        self.ui.btn_send.clicked.connect(self.send_message)
        self.ui.btn_back.clicked.connect(self.close)
        
    def closeEvent(self, event):
        self.parent_window.show()
        event.accept()
        
    # 预留接口
    def send_message(self):
        """发送消息接口"""
        message = self.ui.input_message.text()
        if message:
            # 这里添加实际的消息处理逻辑
            self.ui.text_chat.append(f"你: {message}")
            self.ui.input_message.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 应用样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    floating_window = FloatingWindow()
    floating_window.show()
    
    sys.exit(app.exec_())