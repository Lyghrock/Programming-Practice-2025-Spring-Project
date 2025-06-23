import sys
import os
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QListWidget, QStackedWidget, 
                            QLineEdit, QLabel, QDialog, QHBoxLayout, QVBoxLayout, QFrame,
                            QListWidgetItem, QSizePolicy, QTextEdit, QSplitter, QComboBox,
                            QFileDialog, QMenu, QAction, QGridLayout, QGroupBox, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect, QSettings, QSize
from PyQt5.QtGui import (QIcon, QFont, QMouseEvent, QPainter, QColor, QPen, QBrush, 
                         QPixmap, QRegion, QImage, QPalette, QPainterPath, QLinearGradient)

class BackgroundManager:
    """背景管理器，负责加载、管理和切换背景"""
    def __init__(self):
        self.backgrounds = {}
        self.current_bg = None
        self.default_bg = None
        self.current_bg_name = None
        
    def load_default_backgrounds(self):
        """创建一些默认背景（纯色）"""
        # 创建纯色背景
        self.add_background("浅蓝色", self.create_solid_bg(QColor(173, 216, 230, 180)))
        self.add_background("浅粉色", self.create_solid_bg(QColor(255, 182, 193, 180)))
        self.add_background("浅绿色", self.create_solid_bg(QColor(144, 238, 144, 180)))
        self.add_background("半透明白", self.create_solid_bg(QColor(255, 255, 255, 180)))
        
        # 设置默认背景
        self.default_bg = self.backgrounds["浅蓝色"]
        self.current_bg = self.default_bg
        self.current_bg_name = "浅蓝色"
        
    def create_solid_bg(self, color):
        """创建纯色背景"""
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 100, 100, 15, 15)
        painter.end()
        
        return pixmap
    
    def add_background(self, name, pixmap):
        """添加新背景"""
        self.backgrounds[name] = pixmap
        
    def add_background_from_file(self, path):
        """从文件添加背景"""
        if not os.path.exists(path):
            return False
            
        try:
            pixmap = QPixmap(path)
            if pixmap.isNull():
                return False
                
            # 确保背景大小合适
            name = os.path.basename(path)
            self.backgrounds[name] = pixmap
            return True
        except:
            return False
    
    def get_background(self, name=None):
        """获取指定名称的背景，默认返回当前背景"""
        if name is None:
            return self.current_bg
        return self.backgrounds.get(name, self.default_bg)
    
    def set_current_background(self, name):
        """设置当前背景"""
        if name in self.backgrounds:
            self.current_bg = self.backgrounds[name]
            self.current_bg_name = name
            return True
        return False
    
    def get_background_names(self):
        """获取所有背景名称"""
        return list(self.backgrounds.keys())

# ======================== 桌面宠物 ========================
class DesktopPet(QWidget):
    open_main_window = pyqtSignal()
    trigger_translate = pyqtSignal()
    size_changed = pyqtSignal(int, int)
    background_changed = pyqtSignal(str)
    
    change_background = pyqtSignal(str)
    import_background = pyqtSignal()
    reset_background = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化拖动和缩放属性
        self.dragging = False
        self.resizing = False
        self.resize_direction = None
        self.offset = QPoint()
        
        # 背景管理器
        self.bg_manager = BackgroundManager()
        self.bg_manager.load_default_backgrounds()
        
        # 加载保存的设置
        self.settings = QSettings("MyCompany", "DesktopPet")
        saved_size = self.settings.value("window_size", QSize(140, 180))
        saved_bg = self.settings.value("background", "浅蓝色")
        self.initial_aspect_ratio = saved_size.width() / saved_size.height()
        
        # 使用保存的大小或默认大小
        self.setFixedSize(saved_size.width(), saved_size.height())
        
        # 设置背景
        self.bg_manager.set_current_background(saved_bg)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)
        
        # 添加图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setPixmap(self.create_icon())
        
        # 标题文字
        self.title_label = QLabel("学习助手")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2C3E50;
            background-color: transparent;
        """)
        
        title_layout.addWidget(self.icon_label)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        # 功能按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        buttons_layout.setAlignment(Qt.AlignCenter)
        
        # 主界面按钮
        self.btn_main = QPushButton()
        self.btn_main.setIcon(QIcon(self.create_main_icon()))
        self.btn_main.setIconSize(QSize(24, 24))
        self.btn_main.setToolTip("打开主界面")
        self.btn_main.setFixedSize(60, 60)
        self.btn_main.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border-radius: 30px;
                border: 2px solid #2980B9;
            }
            QPushButton:hover {
                background-color: #2980B9;
                border: 2px solid #1F618D;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
        self.btn_main.clicked.connect(self.open_main_window.emit)
        
        # 翻译按钮
        self.btn_translate = QPushButton()
        self.btn_translate.setIcon(QIcon(self.create_translate_icon()))
        self.btn_translate.setIconSize(QSize(24, 24))
        self.btn_translate.setToolTip("屏幕翻译")
        self.btn_translate.setFixedSize(60, 60)
        self.btn_translate.setStyleSheet("""
            QPushButton {
                background-color: #2ECC71;
                color: white;
                border-radius: 30px;
                border: 2px solid #27AE60;
            }
            QPushButton:hover {
                background-color: #27AE60;
                border: 2px solid #1E8449;
            }
            QPushButton:pressed {
                background-color: #1E8449;
            }
        """)
        self.btn_translate.clicked.connect(self.trigger_translate.emit)
        
        buttons_layout.addWidget(self.btn_main)
        buttons_layout.addWidget(self.btn_translate)
        
        # 添加背景区域
        self.bg_frame = QFrame()
        self.bg_frame.setStyleSheet("""
            background-color: transparent;
            border-radius: 20px;
        """)
        bg_layout = QVBoxLayout(self.bg_frame)
        bg_layout.setSpacing(15)
        bg_layout.addLayout(title_layout)
        bg_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(self.bg_frame)
        self.setLayout(main_layout)
        
        # 添加一个关闭按钮
        self.close_btn = QPushButton("×", self)
        self.close_btn.setGeometry(self.width()-35, 5, 30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
                border: 1px solid #C0392B;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        # 添加背景切换按钮
        self.bg_btn = QPushButton("🎨", self)
        self.bg_btn.setGeometry(5, 5, 30, 30)
        self.bg_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
                border: 1px solid #8E44AD;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        self.bg_btn.clicked.connect(self.show_background_menu)
        
        # 创建背景切换菜单
        self.bg_menu = QMenu(self)
        self.bg_menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #D6DBDF;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px 5px 10px;
                color: #2C3E50;
            }
            QMenu::item:selected {
                background-color: #3498DB;
                color: white;
                border-radius: 3px;
            }
        """)
        self.create_background_menu()
        
        # 添加多个缩放手柄
        self.resize_handles = {}
        
        # 右下角手柄
        self.resize_handles["bottom-right"] = QLabel(self)
        self.resize_handles["bottom-right"].setFixedSize(12, 12)
        self.resize_handles["bottom-right"].setStyleSheet("""
            background-color: #4CAF50;
            border: 1px solid #388E3C;
            border-radius: 6px;
        """)
        
        # 右上角手柄
        self.resize_handles["top-right"] = QLabel(self)
        self.resize_handles["top-right"].setFixedSize(12, 12)
        self.resize_handles["top-right"].setStyleSheet("""
            background-color: #2196F3;
            border: 1px solid #0b7dda;
            border-radius: 6px;
        """)
        
        # 左下角手柄
        self.resize_handles["bottom-left"] = QLabel(self)
        self.resize_handles["bottom-left"].setFixedSize(12, 12)
        self.resize_handles["bottom-left"].setStyleSheet("""
            background-color: #FF9800;
            border: 1px solid #F57C00;
            border-radius: 6px;
        """)
        
        # 更新所有手柄位置
        self.update_resize_handles_position()
        
        # 设置鼠标跟踪
        self.setMouseTracking(True)
        for handle in self.resize_handles.values():
            handle.setMouseTracking(True)
            
        # 连接背景切换信号
        self.change_background.connect(self.set_background)
        self.import_background.connect(self.import_bg_from_file)
        self.reset_background.connect(self.reset_bg_to_default)

    def create_background_menu(self):
        """创建背景切换菜单"""
        # 添加默认背景选项
        for bg_name in self.bg_manager.get_background_names():
            action = QAction(bg_name, self)
            action.triggered.connect(lambda checked, name=bg_name: self.change_background.emit(name))
            self.bg_menu.addAction(action)
        
        # 添加分隔线
        self.bg_menu.addSeparator()
        
        # 导入背景选项
        import_action = QAction("导入背景图片...", self)
        import_action.triggered.connect(self.import_background.emit)
        self.bg_menu.addAction(import_action)
        
        # 重置背景选项
        reset_action = QAction("重置为默认背景", self)
        reset_action.triggered.connect(self.reset_background.emit)
        self.bg_menu.addAction(reset_action)
        
    def show_background_menu(self):
        """显示背景切换菜单"""
        self.bg_menu.exec_(self.bg_btn.mapToGlobal(self.bg_btn.rect().bottomLeft()))
        
    def set_background(self, name):
        """设置背景"""
        if self.bg_manager.set_current_background(name):
            self.settings.setValue("background", name)
            self.update()
            self.background_changed.emit(name)
            
    def import_bg_from_file(self):
        """从文件导入背景"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择背景图片", 
            "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            if self.bg_manager.add_background_from_file(file_path):
                bg_name = os.path.basename(file_path)
                self.set_background(bg_name)
                self.create_background_menu()
                
    def reset_bg_to_default(self):
        """重置为默认背景"""
        self.set_background("浅蓝色")
        
    def create_icon(self):
        """创建应用图标"""
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制书本图标
        painter.setPen(QPen(QColor(41, 128, 185), 2))
        painter.setBrush(QBrush(QColor(52, 152, 219, 200)))
        painter.drawRoundedRect(5, 10, 30, 25, 5, 5)
        
        # 绘制书脊
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(41, 128, 185)))
        painter.drawRect(5, 10, 8, 25)
        
        # 绘制书页线
        painter.setPen(QPen(QColor(236, 240, 241), 1))
        for i in range(3):
            y = 15 + i * 5
            painter.drawLine(15, y, 32, y)
        
        # 绘制铅笔
        painter.setPen(QPen(QColor(231, 76, 60), 2))
        painter.drawLine(25, 5, 30, 10)
        painter.setBrush(QBrush(QColor(231, 76, 60)))
        painter.drawEllipse(28, 8, 4, 4)
        
        painter.end()
        return pixmap
    
    def create_main_icon(self):
        """创建主界面图标"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制房子图标
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        
        # 屋顶
        points = [
            QPoint(12, 4),
            QPoint(20, 12),
            QPoint(4, 12)
        ]
        painter.drawPolygon(points)
        
        # 房子主体
        painter.drawRect(8, 12, 8, 8)
        
        # 门
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(189, 195, 199)))
        painter.drawRect(12, 16, 4, 4)
        
        # 窗户
        painter.setBrush(QBrush(QColor(52, 152, 219)))
        painter.drawRect(9, 13, 2, 2)
        painter.drawRect(13, 13, 2, 2)
        
        painter.end()
        return pixmap
    
    def create_translate_icon(self):
        """创建翻译图标"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制地球图标
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(4, 4, 16, 16)
        
        # 绘制经线
        painter.drawArc(4, 4, 16, 16, 0 * 16, 180 * 16)
        
        # 绘制纬线
        painter.drawEllipse(8, 6, 8, 12)
        
        # 绘制A字符号
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(8, 8, 8, 8, Qt.AlignCenter, "A")
        
        # 绘制中文字符
        painter.setFont(QFont("Microsoft YaHei", 8, QFont.Bold))
        painter.drawText(10, 14, 8, 8, Qt.AlignCenter, "文")
        
        # 添加箭头表示翻译
        painter.setPen(QPen(QColor(46, 204, 113), 2))
        painter.drawLine(16, 18, 20, 18)
        painter.drawLine(20, 18, 18, 16)
        painter.drawLine(20, 18, 18, 20)
        
        painter.end()
        return pixmap

    def update_resize_handles_position(self):
        """更新所有缩放手柄位置"""
        # 右下角
        handle = self.resize_handles["bottom-right"]
        handle_size = handle.size()
        handle.move(
            self.width() - handle_size.width() - 5,
            self.height() - handle_size.height() - 5
        )
        
        # 右上角
        handle = self.resize_handles["top-right"]
        handle.move(
            self.width() - handle_size.width() - 5,
            5
        )
        
        # 左下角
        handle = self.resize_handles["bottom-left"]
        handle.move(
            5,
            self.height() - handle_size.height() - 5
        )
        
        # 更新关闭按钮位置
        self.close_btn.move(self.width()-35, 5)
        
        # 更新背景按钮位置
        self.bg_btn.move(5, 5)

    def paintEvent(self, event):
        """绘制背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建圆角矩形路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
        painter.setClipPath(path)
        
        # 绘制背景
        if not self.bg_manager.current_bg.isNull():
            # 缩放背景以适应窗口
            scaled_bg = self.bg_manager.current_bg.scaled(
                self.width(), 
                self.height(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled_bg)
        else:
            # 默认渐变背景
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(52, 152, 219, 180))
            gradient.setColorAt(1, QColor(46, 204, 113, 180))
            painter.fillRect(self.rect(), gradient)
        
        # 添加边框
        painter.setPen(QPen(QColor(189, 195, 199, 150), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0, 0, self.width()-1, self.height()-1, 20, 20)
        
        # 添加阴影效果
        painter.setPen(QPen(QColor(0, 0, 0, 30), 3))
        painter.drawRoundedRect(2, 2, self.width()-4, self.height()-4, 20, 20)
        
        # 调用父类的绘制事件
        super().paintEvent(event)

    def resizeEvent(self, event):
        """窗口大小改变时更新缩放手柄位置"""
        super().resizeEvent(event)
        self.update_resize_handles_position()
        self.size_changed.emit(self.width(), self.height())

    def closeEvent(self, event):
        """关闭窗口时保存当前大小和背景"""
        self.settings.setValue("window_size", self.size())
        self.settings.setValue("background", self.bg_manager.current_bg_name)
        super().closeEvent(event)

    # 鼠标事件实现拖动和缩放
    def mousePressEvent(self, event: QMouseEvent):
        # 检查是否在缩放手柄上按下
        for direction, handle in self.resize_handles.items():
            if handle.geometry().contains(event.pos()):
                self.resizing = True
                self.resize_direction = direction
                self.initial_mouse_pos = event.globalPos()
                self.initial_size = self.size()
                self.initial_position = self.pos()
                return
            
        # 在背景区域拖动
        if event.button() == Qt.LeftButton and event.pos().y() < 100:
            self.dragging = True
            self.offset = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        # 缩放模式
        if self.resizing and self.resize_direction:
            # 计算鼠标移动的距离
            delta = event.globalPos() - self.initial_mouse_pos
            
            # 计算新尺寸（保持最小尺寸）
            min_width, min_height = 120, 150
            
            if self.resize_direction == "bottom-right":
                # 右下角缩放
                new_width = max(self.initial_size.width() + delta.x(), min_width)
                new_height = max(self.initial_size.height() + delta.y(), min_height)
                
                # 保持宽高比
                new_height = int(new_width / self.initial_aspect_ratio)
                self.setFixedSize(new_width, new_height)
                
            elif self.resize_direction == "top-right":
                # 右上角缩放
                new_width = max(self.initial_size.width() + delta.x(), min_width)
                new_height = max(self.initial_size.height() - delta.y(), min_height)
                
                # 保持宽高比
                new_height = int(new_width / self.initial_aspect_ratio)
                
                # 计算新位置（Y坐标改变）
                new_y = self.initial_position.y() + (self.initial_size.height() - new_height)
                
                # 设置新尺寸和位置
                self.setFixedSize(new_width, new_height)
                self.move(self.initial_position.x(), new_y)
                
            elif self.resize_direction == "bottom-left":
                # 左下角缩放
                new_width = max(self.initial_size.width() - delta.x(), min_width)
                new_height = max(self.initial_size.height() + delta.y(), min_height)
                
                # 保持宽高比
                new_height = int(new_width / self.initial_aspect_ratio)
                
                # 计算新位置（X坐标改变）
                new_x = self.initial_position.x() + (self.initial_size.width() - new_width)
                
                # 设置新尺寸和位置
                self.setFixedSize(new_width, new_height)
                self.move(new_x, self.initial_position.y())
            return
            
        # 拖动模式
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
            return
            
        # 设置鼠标样式
        if self.resize_handles["bottom-right"].geometry().contains(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        elif self.resize_handles["top-right"].geometry().contains(event.pos()):
            self.setCursor(Qt.SizeBDiagCursor)
        elif self.resize_handles["bottom-left"].geometry().contains(event.pos()):
            self.setCursor(Qt.SizeBDiagCursor)
        elif event.pos().y() < 100:  # 头部区域
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_direction = None
            self.setCursor(Qt.ArrowCursor)

    # 添加边缘吸附功能
    def moveEvent(self, event):
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        # 获取窗口位置
        pos = self.pos()
        
        # 检查是否靠近屏幕边缘
        margin = 20  # 吸附距离
        
        # 检查左边缘
        if abs(pos.x()) < margin:
            self.move(0, pos.y())
        # 检查右边缘
        elif abs(screen.width() - (pos.x() + self.width())) < margin:
            self.move(screen.width() - self.width(), pos.y())
        # 检查上边缘
        if abs(pos.y()) < margin:
            self.move(pos.x(), 0)
        # 检查下边缘
        elif abs(screen.height() - (pos.y() + self.height())) < margin:
            self.move(pos.x(), screen.height() - self.height())

# ======================== 主窗口类 ========================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("学习助手")
        self.setGeometry(300, 300, 900, 650)
        self.setStyleSheet("""
            background-color: #F5F7FA;
            font-family: 'Segoe UI', 'Microsoft YaHei UI';
        """)
        
        # 加载设置
        self.settings = QSettings("MyCompany", "DesktopPet")
        saved_size = self.settings.value("main_window_size", QSize(900, 650))
        self.resize(saved_size)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # 左侧功能列表
        self.function_list = QListWidget()
        self.function_list.setFixedWidth(200)
        self.function_list.setStyleSheet("""
            QListWidget {
                background-color: #2C3E50;
                border: none;
                font-size: 14px;
                padding: 10px 0;
                color: #ECF0F1;
            }
            QListWidget::item {
                height: 60px;
                padding-left: 20px;
                border-left: 4px solid transparent;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
                color: white;
                border-left: 4px solid #1ABC9C;
                font-weight: bold;
            }
        """)
        
        # 添加功能项
        functions = [
            {"name": "学习练习", "icon": "📚"},
            {"name": "屏幕翻译", "icon": "🌐"},
            {"name": "智能对话", "icon": "💬"},
            {"name": "词典搜索", "icon": "🔍"},
            {"name": "单词本", "icon": "📒"},
            {"name": "更多功能", "icon": "➕"}
        ]
        
        for func in functions:
            item = QListWidgetItem(f"   {func['icon']}  {func['name']}")
            item.setFont(QFont("Microsoft YaHei", 11))
            item.setData(Qt.UserRole, func["name"])
            self.function_list.addItem(item)
        
        # 右侧功能堆栈
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("""
            QStackedWidget, QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
                border: none;
            }
        """)
        
        # 创建功能页面
        self.learning_widget = LearningPracticeWidget()  # 合并的学习练习组件
        self.translate_widget = ScreenTranslateWidget()
        self.chat_widget = ChatWidget()
        self.dict_widget = DictionaryWidget()
        self.wordbook_widget = WordBookWidget()
        self.more_widget = MoreFunctionsWidget()
        
        # 添加到堆栈
        self.stacked_widget.addWidget(self.learning_widget)
        self.stacked_widget.addWidget(self.translate_widget)
        self.stacked_widget.addWidget(self.chat_widget)
        self.stacked_widget.addWidget(self.dict_widget)
        self.stacked_widget.addWidget(self.wordbook_widget)
        self.stacked_widget.addWidget(self.more_widget)
        
        # 连接选择事件
        self.function_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        # 默认选择第一项
        self.function_list.setCurrentRow(0)
        
        # 添加主内容区域
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #F5F7FA; padding: 15px;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加标题栏
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; padding: 15px;")
        title_layout = QHBoxLayout(title_frame)
        
        title_label = QLabel("学习助手")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50;")
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加内容区域
        content_layout.addWidget(title_frame)
        content_layout.addWidget(self.stacked_widget, 1)
        
        main_layout.addWidget(self.function_list)
        main_layout.addWidget(content_frame, 1)
    
    def closeEvent(self, event):
        """保存主窗口大小"""
        self.settings.setValue("main_window_size", self.size())
        super().closeEvent(event)

# ======================== 学习练习组件 ========================
class LearningPracticeWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("学习练习")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1E88E5;")
        layout.addWidget(title)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                border-top: 1px solid #E0E0E0;
                background: white;
            }
            QTabBar::tab {
                background: #F5F7FA;
                border: 1px solid #E0E0E0;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
                color: #555555;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
                color: #1E88E5;
                border-bottom: 2px solid #1E88E5;
            }
            QTabBar::tab:hover {
                background: #E3F2FD;
            }
        """)
        
        # 添加反语学习标签页
        self.anti_language_tab = AntiLanguageTab()
        self.tab_widget.addTab(self.anti_language_tab, "反语学习")
        
        # 添加单词测试标签页
        self.word_test_tab = WordTestTab()
        self.tab_widget.addTab(self.word_test_tab, "单词测试")
        
        layout.addWidget(self.tab_widget, 1)
        self.setLayout(layout)

# ======================== 反语学习标签页 ========================
class AntiLanguageTab(QWidget):
    submit_answer = pyqtSignal(str)
    toggle_favorite = pyqtSignal(int)
    delete_record = pyqtSignal(int)
    load_records = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setSpacing(20)
        
        # 练习卡片区域
        card_frame = QFrame()
        card_frame.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 15px;
            border: 1px solid #E0E0E0;
            padding: 25px;
        """)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setSpacing(20)
        
        # 问题区域
        self.question_label = QLabel("反语")
        self.question_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #333333;
            min-height: 120px;
            padding: 20px;
            background-color: #F8F9FA;
            border-radius: 10px;
            text-align: center;
        """)
        self.question_label.setAlignment(Qt.AlignCenter)
        
        # 选项按钮区域
        options_layout = QGridLayout()
        options_layout.setSpacing(15)
        
        # 创建四个选项按钮
        self.option_buttons = []
        option_styles = [
            "background-color: #4CAF50;",  # 绿色
            "background-color: #2196F3;",  # 蓝色
            "background-color: #FF9800;",  # 橙色
            "background-color: #9C27B0;"   # 紫色
        ]
        
        option_texts = [
            "一",
            "一",
            "一",
            "一"
        ]
        
        for i, (style, text) in enumerate(zip(option_styles, option_texts)):
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    {style}
                    color: white;
                    font-size: 16px;
                    padding: 15px;
                    border-radius: 10px;
                    min-height: 70px;
                    border: 2px solid rgba(0,0,0,0.1);
                    text-align: left;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            self.option_buttons.append(btn)
            
            # 添加到网格布局
            row = i // 2
            col = i % 2
            options_layout.addWidget(btn, row, col)
        
        # 提交按钮
        self.submit_btn = QPushButton("提交答案")
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E88E5;
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        self.submit_btn.setFixedWidth(200)
        
        # 结果反馈
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-size: 18px; min-height: 30px; padding: 10px;")
        self.result_label.setAlignment(Qt.AlignCenter)
        
        # 添加到卡片布局
        card_layout.addWidget(self.question_label)
        card_layout.addLayout(options_layout)
        card_layout.addWidget(self.submit_btn, 0, Qt.AlignCenter)
        card_layout.addWidget(self.result_label)
        
        # 记录区域
        records_frame = QFrame()
        records_frame.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 10px;
            border: 1px solid #E0E0E0;
            padding: 20px;
        """)
        records_layout = QVBoxLayout(records_frame)
        
        records_title = QLabel("学习记录")
        records_title.setStyleSheet("font-weight: bold; font-size: 18px; color: #555555;")
        
        self.records_list = QListWidget()
        self.records_list.setStyleSheet("""
            QListWidget {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 14px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #EEEEEE;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
            }
        """)
        self.records_list.setMinimumHeight(150)
        
        records_layout.addWidget(records_title)
        records_layout.addWidget(self.records_list)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.favorite_btn = QPushButton("⭐ 收藏")
        self.favorite_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFD54F;
                color: #333333;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFCA28;
            }
        """)
        
        self.delete_btn = QPushButton("🗑️ 删除")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF9A9A;
                color: #333333;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
        """)
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #81C784;
                color: #333333;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
        """)
        
        btn_layout.addWidget(self.favorite_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        
        # 主布局
        layout.addWidget(card_frame)
        layout.addWidget(records_frame, 1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # 连接信号
        self.submit_btn.clicked.connect(lambda: self.submit_answer.emit(""))
        self.refresh_btn.clicked.connect(self.load_records.emit)

# ======================== 单词测试标签页 ========================
class WordTestTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setSpacing(20)
        
        # 进度条区域
        progress_frame = QFrame()
        progress_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 10px; padding: 15px;")
        progress_layout = QHBoxLayout(progress_frame)
        
        self.progress_label = QLabel("进度: 0/20")
        self.progress_label.setStyleSheet("font-size: 16px; color: #555555;")
        
        self.progress_bar = QFrame()
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #E0E0E0;
                border-radius: 10px;
                min-height: 20px;
            }
        """)
        self.progress_bar.setFixedHeight(20)
        
        self.progress_fill = QFrame(self.progress_bar)
        self.progress_fill.setGeometry(0, 0, 0, 20)
        self.progress_fill.setStyleSheet("""
            QFrame {
                background-color: #4CAF50;
                border-radius: 10px;
            }
        """)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar, 1)
        layout.addWidget(progress_frame)
        
        # 单词卡片区域
        card_frame = QFrame()
        card_frame.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 15px;
            border: 1px solid #E0E0E0;
            padding: 25px;
        """)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setSpacing(20)
        
        # 单词显示区域
        self.word_label = QLabel("computer")
        self.word_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #333333;
            min-height: 120px;
            padding: 20px;
            background-color: #F8F9FA;
            border-radius: 10px;
            text-align: center;
        """)
        self.word_label.setAlignment(Qt.AlignCenter)
        
        # 单词图片区域
        self.word_image = QLabel()
        self.word_image.setStyleSheet("""
            background-color: #F0F4C3;
            border-radius: 10px;
            min-height: 200px;
        """)
        self.word_image.setAlignment(Qt.AlignCenter)
        self.word_image.setText("单词图片")
        
        # 选项按钮区域
        options_layout = QGridLayout()
        options_layout.setSpacing(15)
        
        # 创建四个选项按钮
        self.option_buttons = []
        option_styles = [
            "background-color: #4CAF50;",  # 绿色
            "background-color: #2196F3;",  # 蓝色
            "background-color: #FF9800;",  # 橙色
            "background-color: #9C27B0;"   # 紫色
        ]
        
        option_texts = [
            "计算机",
            "计算器",
            "计算",
            "电脑"
        ]
        
        for i, (style, text) in enumerate(zip(option_styles, option_texts)):
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    {style}
                    color: white;
                    font-size: 16px;
                    padding: 15px;
                    border-radius: 10px;
                    min-height: 70px;
                    border: 2px solid rgba(0,0,0,0.1);
                    text-align: left;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            self.option_buttons.append(btn)
            
            # 添加到网格布局
            row = i // 2
            col = i % 2
            options_layout.addWidget(btn, row, col)
        
        # 提交按钮
        self.submit_btn = QPushButton("提交答案")
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E88E5;
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        self.submit_btn.setFixedWidth(200)
        
        # 结果反馈
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-size: 18px; min-height: 30px; padding: 10px;")
        self.result_label.setAlignment(Qt.AlignCenter)
        
        # 添加到卡片布局
        card_layout.addWidget(self.word_label)
        card_layout.addWidget(self.word_image)
        card_layout.addLayout(options_layout)
        card_layout.addWidget(self.submit_btn, 0, Qt.AlignCenter)
        card_layout.addWidget(self.result_label)
        
        layout.addWidget(card_frame, 1)
        self.setLayout(layout)
        
        # 更新进度条
        self.update_progress(0)

    def update_progress(self, progress):
        """更新进度条"""
        total = 20
        self.progress_label.setText(f"进度: {progress}/{total}")
        
        # 计算进度条宽度
        bar_width = self.progress_bar.width()
        fill_width = int(bar_width * progress / total)
        self.progress_fill.setGeometry(0, 0, fill_width, 20)

    def resizeEvent(self, event):
        """窗口大小改变时更新进度条"""
        super().resizeEvent(event)
        self.update_progress(0)  # 暂时使用0，实际应传入当前进度

# ======================== 其他功能组件 ========================
class ScreenTranslateWidget(QWidget):
    start_translate = pyqtSignal()
    show_result = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("屏幕翻译")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1E88E5;")
        layout.addWidget(title)
        
        # 说明区域
        desc_frame = QFrame()
        desc_frame.setStyleSheet("""
            background-color: #FFFDE7;
            border-radius: 10px;
            border: 1px solid #FFECB3;
            padding: 20px;
        """)
        desc_layout = QVBoxLayout(desc_frame)
        
        desc_label = QLabel("使用说明：点击下方按钮开始框选翻译区域，系统将自动识别并翻译选定内容")
        desc_label.setStyleSheet("font-size: 16px; color: #555555;")
        desc_label.setWordWrap(True)
        
        tips_label = QLabel("提示：翻译功能目前支持中英互译，请确保网络连接正常")
        tips_label.setStyleSheet("font-size: 15px; color: #F57C00; font-style: italic;")
        tips_label.setWordWrap(True)
        
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(tips_label)
        layout.addWidget(desc_frame)
        
        # 翻译按钮
        self.translate_btn = QPushButton("开始屏幕翻译")
        self.translate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 18px;
                padding: 15px 30px;
                border-radius: 10px;
                min-height: 60px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.translate_btn, 0, Qt.AlignCenter)
        
        # 结果预览
        result_frame = QFrame()
        result_frame.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 10px;
            border: 1px solid #E0E0E0;
        """)
        result_layout = QVBoxLayout(result_frame)
        
        result_title = QLabel("翻译结果")
        result_title.setStyleSheet("""
            font-weight: bold; 
            font-size: 18px; 
            padding: 15px; 
            color: #555555;
            border-bottom: 1px solid #EEEEEE;
        """)
        
        self.result_preview = QTextEdit()
        self.result_preview.setReadOnly(True)
        self.result_preview.setPlaceholderText("翻译结果将显示在这里...")
        self.result_preview.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: none;
                padding: 20px;
                font-size: 16px;
                border-radius: 0 0 10px 10px;
            }
        """)
        
        result_layout.addWidget(result_title)
        result_layout.addWidget(self.result_preview)
        layout.addWidget(result_frame, 1)
        self.setLayout(layout)
        
        # 连接信号
        self.translate_btn.clicked.connect(self.start_translate.emit)

class ChatWidget(QWidget):
    send_message = pyqtSignal(str, str)
    load_history = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("智能对话")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1E88E5;")
        layout.addWidget(title)
        
        # 模型选择区域
        model_frame = QFrame()
        model_frame.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 10px;
            border: 1px solid #E0E0E0;
            padding: 15px;
        """)
        model_layout = QHBoxLayout(model_frame)
        
        model_label = QLabel("选择对话模型:")
        model_label.setStyleSheet("font-size: 16px;")
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["DeepSeek (智能助手)", "小喷子 (幽默模式)"])
        self.model_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                font-size: 15px;
                min-width: 250px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        layout.addWidget(model_frame)
        
        # 聊天区域
        chat_frame = QFrame()
        chat_frame.setStyleSheet("""
            background-color: #FFFFFF;
            border-radius: 10px;
            border: 1px solid #E0E0E0;
        """)
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        # 聊天历史区域
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: none;
                border-bottom: 1px solid #EEEEEE;
                padding: 20px;
                font-size: 15px;
                border-radius: 10px 10px 0 0;
            }
        """)
        self.chat_history.setMinimumHeight(300)
        
        # 输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 0 0 10px 10px;")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 15, 15, 15)
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                padding: 12px;
                font-size: 15px;
            }
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.send_btn = QPushButton("发送")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px 40px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        
        btn_layout.addWidget(self.send_btn)
        
        input_layout.addWidget(self.message_input)
        input_layout.addLayout(btn_layout)
        
        chat_layout.addWidget(self.chat_history, 3)
        chat_layout.addWidget(input_frame, 1)
        
        layout.addWidget(chat_frame, 1)
        self.setLayout(layout)
        
        # 连接信号
        self.send_btn.clicked.connect(self.on_send_clicked)

    def on_send_clicked(self):
        message = self.message_input.toPlainText().strip()
        model = self.model_combo.currentText()
        if message:
            self.send_message.emit(message, model)

class DictionaryWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("词典搜索功能 (待实现)"))
        self.setLayout(layout)

class WordBookWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("单词本功能 (待实现)"))
        self.setLayout(layout)

class MoreFunctionsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("更多功能扩展区域 (待实现)"))
        self.setLayout(layout)

# ======================== 应用入口 ========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    
    # 创建浮窗
    pet = DesktopPet()
    pet.show()
    
    # 创建主窗口
    main_window = MainWindow()
    
    # 连接信号
    pet.open_main_window.connect(main_window.show)
    pet.trigger_translate.connect(lambda: main_window.stacked_widget.setCurrentWidget(main_window.translate_widget))
    
    # 添加关闭按钮功能
    def close_app():
        pet.close()
        main_window.close()
        app.quit()
    
    # 运行应用
    sys.exit(app.exec_())