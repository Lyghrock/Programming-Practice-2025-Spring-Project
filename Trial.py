import sys
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop, asyncSlot

# 引入你的模块和类
import Reverse_Section.reverse_data_storage as v_data
from Reverse_Section.reverse_programme import Language_Learning_Widget  # 按你实际的文件名导入

# --------- Mock 你的 progress_dialog 方便调试 ----------

class MockProgressDialog:
    def __init__(self, parent=None):
        self.parent = parent  # 如果不需要用，可以忽略
    
    def show(self):
        print("[ProgressDialog] show() called")

    def close(self):
        print("[ProgressDialog] close() called")

    def update_progress(self, percent, trait):
        print(f"[ProgressDialog] Progress update: {trait} {percent}%")

# 替换 v_data.ProgressDialog 为 MockProgressDialog
v_data.ProgressDialog = MockProgressDialog

# ---------------------------------------------------------

async def test_initialization():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    widget = Language_Learning_Widget()
    
    # 替换实例里的progress_dialog为mock
    widget.progress_dialog = MockProgressDialog()

    print("🔧 调用 initialization() 异步函数...")
    await widget.initialization()
    print("✅ initialization() 执行完成。")

    app.quit()

if __name__ == "__main__":
    import qasync
    qasync.run(test_initialization())




