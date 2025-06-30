from GIF_selector import get_random_gif

from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QApplication
from PyQt5.QtCore import Qt, QPoint,QTimer
from PyQt5.QtGui import QMovie
from datetime import datetime

class GifController:
    def __init__(self, update_callback, interval_ms=5*60*1000):
        """
        update_callback: 每次换 gif 时要调用的回调
        interval_ms: 换 gif 的间隔，单位毫秒，默认 2 分钟
        """
        self.update_callback = update_callback
        self.timer = QTimer()
        self.timer.timeout.connect(self._change_gif)
        self.timer.start(interval_ms)

    def _change_gif(self):
        now = datetime.now()
        if (now.hour==11 and 30<=now.minute<=60) or (now.hour==18 and 30<=now.minute<=60):
            path = get_random_gif('eating')
            self.update_callback(path)
        elif (now.hour>=22 or now.hour<=6):
            path = get_random_gif('good_night')
            self.update_callback(path)
        else:
            path = get_random_gif('daily_status')
            self.update_callback(path)







class GifPetWindow(QWidget):
    def __init__(self, float_pet_class):
        super().__init__()

        self.gifcontroller = GifController(self.set_gif)

        self.float_pet_class = float_pet_class
        self.float_pet = None

        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setFixedSize(128, 128)

        self.label_gif = QLabel(self)
        self.label_gif.setFixedSize(128, 128)
        self.label_gif.setAlignment(Qt.AlignCenter)
        self.label_gif.setStyleSheet("background: transparent;")

        self.movie = QMovie(get_random_gif('daily_status'))
        self.movie.setScaledSize(self.label_gif.size())
        self.label_gif.setMovie(self.movie)
        self.movie.start()

        self.dragging = False
        self.offset = QPoint()

        # === 新增，用于延迟判断单击还是双击
        self.click_timer = QTimer(self)
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self._on_single_click_timeout)
        self._pending_single_click = False

        #关闭按钮
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 80, 80, 200);
                border: none;
                color: white;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: red;
            }
        """)
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.move(self.width() - 25, 5)
        self.close_btn.hide()
        self.close_btn.clicked.connect(QApplication.quit)

        # 保证窗口移动后按钮位置仍然正确
        self.installEventFilter(self)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # === 延迟判断单击
            self._pending_single_click = True
            self.click_timer.start(250)  # 250ms内等待双击
            
            # 开始拖动
            self.dragging = True
            self.offset = event.globalPos() - self.pos()

    def _on_single_click_timeout(self):
        if self._pending_single_click:
            self.switch_gif()
            self._pending_single_click = False

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)
            if self.float_pet and self.float_pet.isVisible():
                fx = self.x() + self.width()
                fy = self.y()
                self.float_pet.move(fx, fy)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            # === 发生双击，取消单击动画切换
            self._pending_single_click = False
            self.click_timer.stop()

            self.toggle_float_pet()

    def switch_gif(self):
        self.movie.stop()
        self.movie.setFileName(get_random_gif('be_clicked'))
        self.movie.setScaledSize(self.label_gif.size())
        self.movie.start()

    def set_gif(self, gif_path):
        """收到新 gif 路径后，更新播放动画"""
        self.movie.stop()
        self.movie.setFileName(gif_path)
        self.movie.start()

    def toggle_float_pet(self):
        if self.float_pet is None:
            self.float_pet = self.float_pet_class()

            original_moveEvent = self.float_pet.moveEvent

            def new_moveEvent(event):
                original_moveEvent(event)
                if self.float_pet:
                    gx = self.float_pet.x() - self.width()
                    gy = self.float_pet.y()
                    self.move(gx, gy)

            self.float_pet.moveEvent = new_moveEvent

        if not self.float_pet.isVisible():
            x = self.x() + self.width()
            y = self.y()
            self.float_pet.move(x, y)
            self.float_pet.show()
        else:
            self.float_pet.hide()

    
    def enterEvent(self, event):
        self.close_btn.show()

    def leaveEvent(self, event):
        # 延迟隐藏按钮，避免太敏感
        QTimer.singleShot(700, self._check_mouse_out)

    def _check_mouse_out(self):
        if not self.underMouse():
            self.close_btn.hide()

    def resizeEvent(self, event):
        # 始终将关闭按钮保持在右上角
        self.close_btn.move(self.width() - 25, 5)
    
    





