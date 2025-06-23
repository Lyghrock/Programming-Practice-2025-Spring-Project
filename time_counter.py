import time
import threading

import time
import threading

class TimerCore:
    def __init__(self, mode='countup', duration=0):
        self.mode = mode
        self.duration = duration
        self.start_time = None
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            self.start_time = time.time()
            self.running = True

    def stop(self):
        with self._lock:
            self.running = False

    def reset(self):
        with self._lock:
            self.start_time = None
            self.running = False

    def get_time(self):
        with self._lock:
            if not self.running or self.start_time is None:
                return 0, False
            elapsed = int(time.time() - self.start_time)
            if self.mode == 'countup':
                return elapsed, True
            else:
                remaining = max(0, self.duration - elapsed)
                running = remaining > 0
                if not running:
                    self.running = False
                return remaining, running

            
# #用法
# # 初始化倒计时 10 秒
# timer = TimerCore(mode='countdown', duration=10)
# #timer = TimerCore(mode='countup')
# timer.start()

# # 模拟前端每秒拉取一次
# for _ in range(100):
#     current_time, running = timer.get_time()
#     print(f"显示：{current_time:02d}s  正在运行: {running}")
#     time.sleep(1)
