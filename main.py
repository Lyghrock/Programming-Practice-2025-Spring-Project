import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget  # 或 PyQt6

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Hello PyQt")
window.setGeometry(100, 100, 280, 80)

label = QLabel('<font color="blue">Hello, PyQt!</font>', parent=window)
label.move(60, 15)

window.show()
sys.exit(app.exec_())  # PyQt6 是 exec()
