import reverse_data_storage as v_data
import reverse_function as v_func
from reverse_function import AUDIO_ADDRESS,INITIAL_SCALE

import os
import sqlite3

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QTextEdit, QLabel
)
import PyQt5.QtCore as Qt

import aiohttp
import asyncio  

from qasync import QEventLoop, asyncSlot

SIMUL_BOUND_VOICE = 20
SIMUL_BOUND_DEFINITION = 8

class Language_Learning_Widget(QWidget):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags()):
        super().__init__(parent)
        self.setWindowTitle("Language Learning Module")
        
        v_data.Initial_Word_list = v_func.load_word_list()
        
        Qt.QTimer.singleShot(0,lambda: asyncio.ensure_future(self.initialization()))
        
        # 建立Word_Query类，来动态管理这些数据
        
        
        # 维护一个计数器+timer动态更新下载进度？
        
    
    @asyncSlot
    async def initialization(self):
    
    # 调用百度API获得单词对应的语音文件，存入本地
        audio_map = await self.initialize_voice_pack()
    
    # 调用爬虫程序从汉典(http网址)中爬取definition，存入.txt
        defin_map = await self.initialize_word_definition()
        
    # 建立SQLite数据库来统一存放这些初始化的单词     
        
        translation_map = dict()
        for word in v_data.Initial_Word_list:
            temp_res = v_func.translate_text(word)
            try:
                assert temp_res is not None
                translation_map[word] = temp_res
            except Exception as e:  
                print(f"Blank Translation??? : {e}")
                translation_map[word] = None
        
        parameters_for_SQLite = {
            "audio" : audio_map, 
            "definition" : defin_map, 
            "translation" : translation_map,
            "picture" : {word : None for word in v_data.Initial_Word_list}
        }
        
        try:    v_func.update_database(parameters_dict = parameters_for_SQLite)
        except Exception as error:  print(f"Error occurs when storing .db: {error}")
        
    
    @asyncSlot
    async def initialize_voice_pack(self, language = str()):
        
        audio_address_map = dict()
        if v_func.check_data_exist():
            print("atabase is already downloaded!")
            
            for word in v_data.Initial_Word_list:
                audio_address_map[word] = f"{word}_{language}.mp3"
            return audio_address_map
        
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
            
            async def simul_task(word, language):
                async with asyncio.Semaphore(SIMUL_BOUND_VOICE):
                    try:
                        judge_res = await v_func.text_to_speech(request_agent, token, text = word, 
                            lang = language, filename = f"{word}_{language}.mp3")
                        if judge_res:   audio_address_map[word] = f"{word}_{language}.mp3"
                    except Exception as error:
                        print(f"Text_to_Voice Error: {word} has {error}")
                        audio_address_map[word] = None
            
            all_tasks = [ simul_task(current_word, language) 
                    for current_word in v_data.Initial_Word_list ]
                
            await asyncio.gather(*all_tasks)
        
        return audio_address_map
            
    @asyncSlot
    async def initialize_word_definition(self):

        definition_map = dict() 
        if v_func.check_data_exist():
            try:
                with open(v_data.DEFINITION_ADDRESS,"r",encoding = "utf-8") as f:
                    for line in f.readlines():
                        w, d = line.split("\t")[0],line.split('\t')[1]
                        definition_map[w] = d
            except Exception as e:  print(f"Load_def Error: {e}")
            
            return definition_map

        async with aiohttp.ClientSession(headers=v_data.REQUEST_HEADERS) as session:

            async def simul_task(word):
                async with asyncio.Semaphore(SIMUL_BOUND_DEFINITION):
                    try:
                        def_str = await v_func.text_to_definition(session, word)
                        if def_str:    definition_map[word] = def_str
                    except Exception as error:
                        print(f"Text_to_Definition Error: {word} has {error}")
                        definition_map[word] = str()

            # 构建并发任务
            all_tasks = [simul_task(word) for word in v_data.Initial_Word_list]
            await asyncio.gather(*all_tasks)
            
            v_func.save_definition_data(definition_map)

        return definition_map
                
                