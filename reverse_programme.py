import reverse_data_storage as v_data
import reverse_function as v_func
from reverse_function import AUDIO_ADDRESS,INITIAL_SCALE

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QTextEdit, QLabel
)
import PyQt5.QtCore as Qt

import aiohttp
import asyncio  

from qasync import QEventLoop, asyncSlot

SIMUL_BOUND = 20
    # 这个是预下载的word_bank原始文件

class Language_Learning_Widget(QWidget):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags()):
        super().__init__(parent)
        self.setWindowTitle("Language Learning Module")
        
        Qt.QTimer.singleShot(0,lambda: asyncio.ensure_future(self.initialization()))
        
        # 建立Word_Query类来管理这些数据
        
        
    
    @asyncSlot
    async def initialization(self):
    
    # 调用百度API获得单词对应的语音文件，存入本地
        await self.initialize_voice_pack()
    
    # 调用爬虫程序从汉典(http网址)中爬取definition，存入.txt
        await self.initialize_vocabulary_data()
        
    # 建立SQLite数据库来统一存放这些单词
        
    
    @asyncSlot
    async def initialize_voice_pack(self):
        
        if v_func.check_voice_directory():
            print("Voice Database is already downloaded!")
            return 
        
        # 此处建立一个异步HTTP客户端会话管理器(通常命名为session)（aiohttp库的引入）
            # 用来代替requests库来发送异步请求——见reverse_fucntion
        
        async with aiohttp.ClientSession(headers = v_data.REQUEST_HEADERS) as request_agent:
            # Use request_agent to give requests to http:
            token = await v_func.get_voice_token(session = request_agent)
            if not token:   
                # Notice: token provided by Baidu has a validity for 30 days, which means 30 days 
                    # later you need to run this get_token part again!
                print("Fail to load API_url, token unaccessible. Please check your Account.")
            
            # Set sveral different tasks simultaneously to enhance effiency:
            v_data.Initial_Word_list = v_func.load_word_list(v_data.WORD_BANK_ADDRESS)
            
            async def simul_task(word, language):
                async with asyncio.Semaphore(SIMUL_BOUND):
                    await v_func.text_to_speech(request_agent, token, text = word, 
                        lang = language, filename = f"{word}_{language}.mp3")
            
            all_tasks = list()
            for current_word in v_data.Initial_Word_list:
                all_tasks.append(simul_task(current_word,"zh"))
                
            await asyncio.gather(*all_tasks)
            
    @asyncSlot
    async def initialize_vocabulary_data(self):
        pass
            
            
            