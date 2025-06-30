from PIL import Image
import pytesseract
import os
from openai import OpenAI
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QRubberBand, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QTimer
from PyQt5.QtGui import QGuiApplication,QPainter, QColor,QPen


os.environ["TMP"] = "D:\\Desk_Pet_Data_Storage\\Temp"
os.environ["TEMP"] = "D:\\Desk_Pet_Data_Storage\\Temp"

# 如果这个路径不存在，先创建
if not os.path.exists("D:\\Desk_Pet_Data_Storage\\Temp"):
    os.makedirs("D:\\Desk_Pet_Data_Storage\\Temp")

pytesseract.pytesseract.tesseract_cmd = r"../Tesseract/tesseract.exe"


def extract_text_from_image(image_path: str):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="eng")  # 识别英文
        return text.strip()
    except Exception as e:
        return f"发生错误：{e}"


my_prompt = """
你将担任一个翻译官，对一段英语进行翻译
请尝试理解这段英语的内容，结合语境文意进行翻译
如果这段内容非常学术，请使用学术的方式翻译，使用正规的专有名词
由于给你的文段由图像识别产生，可能会包含一些混乱字符或错误单词，请从整体上把握文段的大意，并对可能的缺失部分进行推理与补全
可能需要抛弃一部分乱字符不翻译
"""

output_format ="""
输出必须有且仅有对原文段的中文翻译，要求语句流畅，语义明确
不要输出除了翻译之外的东西
"""


prompt = my_prompt+output_format
API_KEY = "sk-0fd83851c92841c2a7b5f96fffa4e3bd" 
model_name = "deepseek-chat"
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def get_translation(client: OpenAI, model_name: str, text: str):
    try:
        response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": f"Translate the following English text into Chinese:\n{text}"
            }
        ],
            stream=False,
            temperature=0
        )
        chinese = response.choices[0].message.content.strip()
        return chinese
    except Exception as e:
        print(f"翻译请求失败：{e}")
        return f"翻译请求失败：{e}"

def translate(image_path: str) -> str:  
    text = extract_text_from_image(image_path)
    chinese = get_translation(client,model_name,text)
    os.remove(image_path)
    return chinese


# image_path = r"D:\\python\\Practice of programming\\Py_Qt\\25105d4ba5bb718f0532c9411c59bc5.jpg"
# text = extract_text_from_image(image_path)
# chinese = get_translation(client,model_name,text)
# print(chinese)


class ScreenSelector_For_Translator(QWidget):
    def __init__(self,on_finished_callback):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        self.origin = QPoint()
        self.current_pos = QPoint()
        self.selecting = False
        self.on_finished_callback = on_finished_callback

    def paintEvent(self, event):
        painter = QPainter(self)
        # 画半透明遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 50))
        if self.selecting:
            # 只画矩形边框，不填充
            pen = QPen(QColor(255, 0, 0), 4)  # DodgerBlue，线宽2
            painter.setPen(pen)
            rect = QRect(self.origin, self.current_pos).normalized()
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.current_pos = event.pos()
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            self.update()

            rect = QRect(self.origin, event.pos()).normalized()

            # 隐藏窗口，避免自己遮挡截图
            self.hide()

            # 延时截图，确保窗口隐藏生效
            QTimer.singleShot(50, lambda: self.capture_and_close(rect))

    def capture_and_close(self, rect):
        screen = QGuiApplication.screens()[0]
        full_screenshot = screen.grabWindow(0)
        cropped = full_screenshot.copy(rect)

        save_dir = r"D:\Desk_Pet_Data_Storage\Temp"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "screenshot.png")
        success = cropped.save(save_path, "png")
        #print(f"截图保存 {'成功' if success else '失败'}，路径：{save_path}")

        #print(translate(save_path))
        if self.on_finished_callback:
            self.on_finished_callback()
        self.close()


class ScreenSelector_For_ScreenSelect(QWidget):
    def __init__(self,on_finished_callback):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        self.origin = QPoint()
        self.current_pos = QPoint()
        self.selecting = False
        self.on_finished_callback=on_finished_callback

    def paintEvent(self, event):
        painter = QPainter(self)
        # 画半透明遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 10))
        if self.selecting:
            # 只画矩形边框，不填充
            pen = QPen(QColor(255, 0, 0), 4)  # DodgerBlue，线宽2
            painter.setPen(pen)
            rect = QRect(self.origin, self.current_pos).normalized()
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.current_pos = event.pos()
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            self.update()

            rect = QRect(self.origin, event.pos()).normalized()

            # 隐藏窗口，避免自己遮挡截图
            self.hide()

            # 延时截图，确保窗口隐藏生效
            QTimer.singleShot(50, lambda: self.capture_and_close(rect))

    def capture_and_close(self, rect):
        screen = QGuiApplication.screens()[0]
        full_screenshot = screen.grabWindow(0)
        cropped = full_screenshot.copy(rect)
        QApplication.clipboard().setPixmap(cropped)
        if self.on_finished_callback:
            self.on_finished_callback()
        self.close()

#使用方式如下

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("截图测试")
        layout = QVBoxLayout()
        btn = QPushButton("开始截图")
        btn.clicked.connect(self.start_screenshot)
        layout.addWidget(btn)
        self.setLayout(layout)

    def start_screenshot(self):
        self.hide()
        self.selector = ScreenSelector_For_Translator()   #这里换一下For什么就行
        self.selector.showFullScreen()
        QTimer.singleShot(100, self.selector.raise_)
        QTimer.singleShot(100, self.selector.activateWindow)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())