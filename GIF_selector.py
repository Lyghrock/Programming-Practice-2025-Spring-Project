import os, random
from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtGui import QMovie
import sys



class GifLibrary:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.gif_dict = {}
        self.group_dict = {}
        self._load_gifs()

    def _load_gifs(self):
        for root, dirs, files in os.walk(self.base_dir):
            group_name = os.path.relpath(root, self.base_dir)
            for file in files:
                if file.endswith(".gif"):
                    name = os.path.splitext(file)[0]
                    full_path = os.path.join(root, file)
                    self.gif_dict[name] = full_path
                    self.group_dict.setdefault(group_name, []).append((name, full_path))

    def get(self, name):
        """按名字获取某个 gif 路径"""
        return self.gif_dict.get(name)

    def get_group(self, group):
        """按组获取所有 (name, path)"""
        return self.group_dict.get(group, [])

    def list_all(self):
        return list(self.gif_dict.keys())

    def list_groups(self):
        return list(self.group_dict.keys())



lib = GifLibrary("..\\gif_source")

def get_random_gif(group_name: str) -> str:
    """return the path of a random gif from a group"""
    group = lib.get_group(group_name)
    i = random.randint(0,len(group)-1)
    name, path = group[i]
    return path



class GifPlayer(QLabel):
    def __init__(self, gif_path):
        super().__init__()
        self.movie = QMovie(gif_path)
        self.setMovie(self.movie)
        self.movie.start()
        self.setFixedSize(100, 100)
        self.setScaledContents(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    lib = GifLibrary("..\\gif_source")
    print("可用GIF：", lib.list_all())
    print("可用分组：", lib.list_groups())
    print("emotion组：", lib.get_group("be_clicked"))

    gif_path =  get_random_gif('after_task')
    if gif_path:
        player = GifPlayer(gif_path)
        player.show()

    sys.exit(app.exec_())