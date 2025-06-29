# import asyncio
# from Reverse_Section.reverse_function import get_data_from_database
# from Reverse_Section.reverse_data_storage import WORD_BANK_ADDRESS

# async def test_get_data():
#     test_word = "周成豫"# 你知道在数据库中存在的一个单词
#     result = await get_data_from_database(test_word, address = vd)

#     if result:
#         print(f"✅ 查询成功：{test_word}")
#         for key, value in result.items():
#             print(f"{key}: {value}")
#     else:
#         print(f"❌ 查询失败，数据库中找不到单词：{test_word}")

# # 主运行入口（用于手动测试）
# if __name__ == "__main__":
#     asyncio.run(test_get_data())

import sys
import asyncio
from Reverse_Section import reverse_data_storage as v_data
from Reverse_Section import reverse_function as v_func
from Reverse_Section.reverse_programme import Language_Learning_Widget

from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop


# 继承你的类，重写 __init__，屏蔽 UI 初始化代码
class TestWidget(Language_Learning_Widget):
    def __init__(self):
        # 不调用super().__init__()以避免UI和QTimer干扰
        # 手动设置必须属性
        self.progress_dialog = self.MockProgressDialog()
        self.set_all_buttons_enabled_called = []

        # 载入测试词表
        v_data.Initial_Word_list = v_func.load_word_list(mode="test")

    class MockProgressDialog:
        def show(self):
            print("[MockProgressDialog] show()")
        def close(self):
            print("[MockProgressDialog] close()")
        def update_progress(self, percent, trait):
            print(f"[MockProgressDialog] update_progress {trait}: {percent}%")

    def set_all_buttons_enabled(self, enabled: bool):
        print(f"[TestWidget] set_all_buttons_enabled({enabled}) called")
        self.set_all_buttons_enabled_called.append(enabled)

async def test_initialization(widget):
    try:
        await widget.initialization()
        print("✅ initialization ran successfully")
    except Exception as e:
        print(f"❌ initialization raised exception: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    # asyncio.set_event_loop(loop)

    widget = TestWidget()

    with loop:
        loop.run_until_complete(test_initialization(widget))