import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen
from UI_File.floating_window_ui import Ui_FloatPet
from UI_File.antonym_learning_ui import Ui_Study
from UI_File.screen_translate_ui import Ui_Translation
from UI_File.chat_window_ui import Ui_Chat

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
        
        # 存储功能窗口引用
        self.study_window = None
        self.translation_window = None
        self.chat_window = None
        
        # 初始化位置
        self.dragging = False
        self.offset = QPoint()
        
        # 设置拖动区域样式
        self.drag_area.setStyleSheet("""
            QLabel {
                background-color: #5CACEE;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid #3A5FCD;
            }
        """)
        
    def paintEvent(self, event):
        """绘制圆角和边框"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#3A5FCD"), 1))
        painter.setBrush(QColor(240, 240, 240, 200))
        painter.drawRoundedRect(self.rect(), 10, 10)
        
    def mousePressEvent(self, event):
        # 只在拖动区域允许拖动
        if event.button() == Qt.LeftButton and self.drag_area.geometry().contains(event.pos()):
            self.dragging = True
            self.offset = event.globalPos() - self.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            # 添加边缘吸附逻辑
            self.attach_to_edge()
    
    def attach_to_edge(self):
        # 边缘吸附实现
        screen_rect = QApplication.desktop().availableGeometry()
        window_rect = self.geometry()
        
        # 左边缘吸附
        if abs(window_rect.left() - screen_rect.left()) < 20:
            self.move(screen_rect.left(), window_rect.top())
        # 右边缘吸附
        elif abs(screen_rect.right() - window_rect.right()) < 20:
            self.move(screen_rect.right() - window_rect.width(), window_rect.top())
        # 上边缘吸附
        elif abs(window_rect.top() - screen_rect.top()) < 20:
            self.move(window_rect.left(), screen_rect.top())
        # 下边缘吸附
        elif abs(screen_rect.bottom() - window_rect.bottom()) < 20:
            self.move(window_rect.left(), screen_rect.bottom() - window_rect.height())
    
    def show_study(self):
        self.hide()
        if not self.study_window:
            self.study_window = StudyWindow(self)
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

class StudyWindow(QWidget, Ui_Study):
    def __init__(self, float_pet):
        super().__init__()
        self.setupUi(self)
        self.float_pet = float_pet
        self.setWindowTitle("学习中心")
        
        # 连接按钮信号
        self.btn_back.clicked.connect(self.close)
        self.btn_switch_mode.clicked.connect(self.switch_mode)
        self.btn_add_to_vocab.clicked.connect(self.add_to_vocab)
        self.btn_save.clicked.connect(self.save_result)
        self.btn_abandon.clicked.connect(self.close)
        
        # 初始化模式
        self.current_mode = "anti_language"  # "anti_language" 或 "word_test"
        self.update_mode_ui()
        
        # 连接选项按钮
        self.btn_option1.clicked.connect(lambda: self.check_answer(1))
        self.btn_option2.clicked.connect(lambda: self.check_answer(2))
        self.btn_option3.clicked.connect(lambda: self.check_answer(3))
        self.btn_option4.clicked.connect(lambda: self.check_answer(4))
        
    def switch_mode(self):
        """切换反语学习和单词测试模式"""
        if self.current_mode == "anti_language":
            self.current_mode = "word_test"
        else:
            self.current_mode = "anti_language"
        self.update_mode_ui()
    
    def update_mode_ui(self):
        """根据当前模式更新UI"""
        if self.current_mode == "anti_language":
            self.btn_switch_mode.setText("切换到单词测试")
            self.lbl_mode.setText("当前模式: 反语学习")
            self.lbl_question.setText("请输入要反转的句子:")
            self.lbl_word_image.setText("反语练习区域")
        else:
            self.btn_switch_mode.setText("切换到反语学习")
            self.lbl_mode.setText("当前模式: 单词测试")
            self.lbl_question.setText("请选择正确的单词含义:")
            self.lbl_word_image.setText("单词图片显示区域")
        
        # 重置选项按钮文本
        for i, btn in enumerate([self.btn_option1, self.btn_option2, 
                                self.btn_option3, self.btn_option4], 1):
            btn.setText(f"选项 {chr(64+i)}")
    
    def check_answer(self, option):
        """检查答案（接口）"""
        print(f"检查答案接口调用: 模式={self.current_mode}, 选项={option}")
        # 这里应该调用后端接口检查答案
        # 暂时模拟正确/错误
        is_correct = option == 1  # 假设第一个选项总是正确
        
        if is_correct:
            QMessageBox.information(self, "结果", "回答正确!")
        else:
            QMessageBox.warning(self, "结果", "回答错误!")
    
    def add_to_vocab(self):
        """添加到单词本（接口）"""
        print("添加到单词本接口调用")
        QMessageBox.information(self, "提示", "已添加到单词本!")
    
    def save_result(self):
        """保存结果（接口）"""
        print("保存结果接口调用")
        self.close()
    
    def closeEvent(self, event):
        self.float_pet.show_float_pet()
        event.accept()

class TranslationWindow(QWidget, Ui_Translation):
    def __init__(self, float_pet):
        super().__init__()
        self.setupUi(self)
        self.float_pet = float_pet
        self.setWindowTitle("屏幕翻译")
        self.btn_back.clicked.connect(self.close)
        self.btn_select_area.clicked.connect(self.select_area)
        
    def select_area(self):
        # 屏幕框选接口
        print("框选区域接口调用")
        # 模拟翻译结果
        self.text_result.setText("这是一段翻译后的文本\nThis is a translated text")
        
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
        self.combo_chat_type.addItem("DeepSeek")
        self.combo_chat_type.addItem("小喷子")
        
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
            
            # 模拟AI回复
            if chat_type == "DeepSeek":
                reply = "DeepSeek: 你好！我是DeepSeek助手，很高兴为你服务。"
            else:
                reply = "小喷子: 哼！你问这个干嘛？"
            
            self.text_chat.append(f"<b>{chat_type}:</b> {reply}")
    
    def closeEvent(self, event):
        self.float_pet.show_float_pet()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    float_pet = FloatPet()
    float_pet.show()
    sys.exit(app.exec_())