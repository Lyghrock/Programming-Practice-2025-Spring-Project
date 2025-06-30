import sys
from qasync import QEventLoop
import asyncio
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QGuiApplication, QScreen, QPixmap, QClipboard
from UI_File.floating_window_ui import Ui_FloatPet
from UI_File.screen_translate_ui import Ui_Translation
from UI_File.chat_window_ui import Ui_Chat
from translator_functions import translate, ScreenSelector_For_ScreenSelect, ScreenSelector_For_Translator

from Reverse_Section.reverse_programme import Language_Learning_Widget
import Reverse_Section.reverse_data_storage as v_data
from LLM_chating_functions import get_DeepSeek_response
from pet_player import GifPetWindow


class FloatPet(QWidget, Ui_FloatPet):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 连接按钮信号
        self.btn_study.clicked.connect(self.show_study)
        self.btn_translation.clicked.connect(self.show_translation)
        self.btn_chat.clicked.connect(self.show_chat)
        self.btn_screenshot.clicked.connect(self.take_screenshot)  # 新增截屏功能
        
        # 存储功能窗口引用
        self.study_window = None
        self.translation_window = None
        self.chat_window = None
        
        # 初始化位置
        self.dragging = False
        self.offset = QPoint()

    def mousePressEvent(self, event):
    # 整个窗口都可拖动（移除原有的区域限制）
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.pos()
        
    def paintEvent(self, event):
        """绘制圆角和边框"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#3A5FCD"), 1))
        painter.setBrush(QColor(240, 240, 240, 200))
        painter.drawRoundedRect(self.rect(), 10, 10)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.attach_to_edge()  # 释放鼠标时进行边缘吸附
    
    def attach_to_edge(self):
        # 边缘吸附实现（改进版）
        screen_rect = QApplication.desktop().availableGeometry()
        window_rect = self.geometry()
        
        # 计算窗口到各边缘的距离
        left_dist = window_rect.left() - screen_rect.left()
        right_dist = screen_rect.right() - window_rect.right()
        top_dist = window_rect.top() - screen_rect.top()
        bottom_dist = screen_rect.bottom() - window_rect.bottom()
        
        # 设置吸附阈值
        threshold = 20
        
        # 确定新的位置（初始为当前位置）
        new_x = window_rect.x()
        new_y = window_rect.y()
        
        # 检查是否需要水平吸附
        if min(left_dist, right_dist) < threshold:
            if left_dist < right_dist:
                new_x = screen_rect.left()  # 吸附到左边缘
            else:
                new_x = screen_rect.right() - window_rect.width()  # 吸附到右边缘
        
        # 检查是否需要垂直吸附
        if min(top_dist, bottom_dist) < threshold:
            if top_dist < bottom_dist:
                new_y = screen_rect.top()  # 吸附到上边缘
            else:
                new_y = screen_rect.bottom() - window_rect.height()  # 吸附到下边缘
        
        # 如果位置有变化则移动窗口
        if new_x != window_rect.x() or new_y != window_rect.y():
            self.move(new_x, new_y)
    
    def show_study(self):
        self.hide()
        if not self.study_window:
            self.study_window = Language_Learning_Widget(parent = self)
        self.study_window.show()
    
    def show_translation(self):
        self.hide()
        if not self.translation_window:
            self.translation_window = TranslationWindow(self)
        self.translation_window.show()
    
    def show_chat(self):
        self.hide()
        if not self.chat_window:
            self.chat_window = ChatWindow(self)
        self.chat_window.show()
    
    def show_float_pet(self):
        self.show()
        
    # 新增截屏功能
    def take_screenshot(self):
        def after_screenshot():
            self.show()
        
        self.hide()  # 隐藏桌宠窗口
        self.selector = ScreenSelector_For_ScreenSelect(after_screenshot)   
        self.selector.showFullScreen()
        QTimer.singleShot(100, self.selector.raise_)
        QTimer.singleShot(100, self.selector.activateWindow)
        
    

class TranslationWindow(QWidget, Ui_Translation):
    def __init__(self, float_pet):
        super().__init__()
        self.setupUi(self)
        self.float_pet = float_pet
        self.setWindowTitle("屏幕翻译")
        self.btn_back.clicked.connect(self.close)
        self.btn_select_area.clicked.connect(self.select_area)
        
    def select_area(self):
        def after_screenshot():
            print("截图完成，开始翻译")
            self.text_result.setText("截图完成，开始翻译")
            self.show()
            QTimer.singleShot(100, self.run_translation)
            
        self.hide()
        self.selector = ScreenSelector_For_Translator(on_finished_callback=after_screenshot)
        self.selector.showFullScreen()
        QTimer.singleShot(100, self.selector.raise_)
        QTimer.singleShot(100, self.selector.activateWindow)
        
    def run_translation(self):
        self.chinese = translate("D:\\Desk_Pet_Data_Storage\\Temp\\screenshot.png")
        self.text_result.setText(self.chinese)
    def closeEvent(self, event):
        self.float_pet.show_float_pet()
        event.accept()

class ChatWindow(QWidget, Ui_Chat):
    def __init__(self, float_pet):
        super().__init__()
        self.setupUi(self)
        self.float_pet = float_pet
        self.setWindowTitle("智能对话")
        
        # 设置聊天对象选项
        #self.combo_chat_type.addItem("DeepSeek")
        #self.combo_chat_type.addItem("小喷子")
        
        # 连接信号
        self.btn_back.clicked.connect(self.close)
        self.btn_send.clicked.connect(self.send_message)
        
    def send_message(self):
        # 发送消息接口
        message = self.input_message.text()
        chat_type = self.combo_chat_type.currentText()
        
        if message:
            # 在聊天记录中添加用户消息
            self.text_chat.append(f"<b>你:</b> {message}")
            self.input_message.clear()
            self.text_chat.append(f"<b>{chat_type}:</b> 思考中...")
            # 模拟AI回复
            # if chat_type == "DeepSeek":
            #     reply = "DeepSeek: 你好！我是DeepSeek助手，很高兴为你服务。"
            # else:
            #     reply = "小喷子: 哼！你问这个干嘛？"
            def show_reply():
                reply = get_DeepSeek_response(message)
                self.text_chat.append(f"<b>{chat_type}:</b> {reply}")
            QTimer.singleShot(100, show_reply)
    
    def closeEvent(self, event):
        self.float_pet.show_float_pet()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)

    # 使用 qasync 的事件循环
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # float_pet = FloatPet()
    # float_pet.show()
    window = GifPetWindow(FloatPet)
    window.show()

    with loop:
        loop.run_forever()