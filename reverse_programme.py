import reverse_function as v_func
from reverse_function import AUDIO_ADDRESS

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QTextEdit, QLabel
)
import PyQt5.QtCore as Qt

import aiohttp
import asyncio  

from qasync import QEventLoop, asyncSlot

SIMUL_BOUND = 20
WORD_BANK_ADDRESS = "D:\\Python_Audio_Processing\\Word_bank\\Initialize_word_bank.txt"

class Language_Learning_Widget(QWidget):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags()):
        super().__init__(parent)
        self.setWindowTitle("Language Learning Module")
        
        Qt.QTimer.singleShot(0,self.initialize_voice_pack)
        
    
    @asyncSlot
    async def initialization(self):
        await self.initialize_voice_pack()
        await self.initialize_vocabulary_data()
    
    @asyncSlot
    async def initialize_voice_pack(self):
        
        # 此处建立一个异步HTTP客户端会话管理器(通常命名为session)（aiohttp库的引入）
            # 用来代替requests库来发送异步请求——见reverse_fucntion
        
        async with aiohttp.ClientSession() as request_agent:
            # Use request_agent to give requests to http:
            token = await v_func.get_token(session = request_agent)
            if not token:   
                # Notice: token provided by Baidu has a validity for 30 days, which means 30 days 
                    # later you need to run this get_token part again!
                print("Fail to load API_url, token unaccessible. Please check your Account.")
                
            word_bank = list()
            with open(WORD_BANK_ADDRESS, "r", encoding="utf-8") as file:
                word_bank = [line.strip() for line in file.readlines()[:5000]]
            
            # Set sveral different tasks simultaneously to enhance effiency:
            
            async def simul_task(word, language):
                async with asyncio.Semaphore(SIMUL_BOUND):
                    await v_func.text_to_speech(request_agent, token, text = word, 
                        lang = language, filename = f"{word}_{language}.mp3")
            
            all_tasks = list()
            for current_word in word_bank:
                all_tasks.append(simul_task(current_word,"zh"))
                
            await asyncio.gather(*all_tasks)
            
    @asyncSlot
    async def initialize_vocabulary_data():
        pass
            
            
            