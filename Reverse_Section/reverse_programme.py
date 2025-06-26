from . import reverse_data_storage as v_data
from . import reverse_function as v_func

import os
import sqlite3
import random
import math

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QTextEdit, QLabel, 
    QMessageBox, QInputDialog
)
from PyQt5.QtCore import (
    QTimer, Qt
)
from PyQt5.uic import loadUi

import aiohttp
import asyncio  
from typing import Callable, Optional
from UI_File.Reverse_Widget.Language_Learning_Widget import Ui_Main_Window
from UI_File.Reverse_Widget.Test_Widget import Ui_Test_Window
from UI_File.Reverse_Widget.Search_Widget import Ui_Word_Search
from UI_File.Reverse_Widget.Finish_Test_Widget import Ui_Finish_Test
from UI_File.Reverse_Widget.Word_Bank_Widget import Ui_My_Word_Brochure



from qasync import QEventLoop, asyncSlot

SIMUL_BOUND_VOICE = 5
SIMUL_BOUND_DEFINITION = 8

SIMUL_BATCH_SIZE = 30  
INTERVAL_BETWEEN_BATCHES = 0.6 

class Language_Learning_Widget(QWidget,Ui_Main_Window):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags()):
        super().__init__()
        self.setupUi(self)
        self.Upper_parent = parent
        
        # 维护一个计数进度条类，动态更新下载进度————（控件由loadUi实现）
        self.progress_dialog = v_data.ProgressDialog(parent = self)
        self.set_all_buttons_enabled(False)
        
        v_data.Initial_Word_list = v_func.load_word_list(mode = "test")
        
        QTimer.singleShot(0, lambda : asyncio.ensure_future(self.initialization()))
    
    @asyncSlot()
    async def initialization(self):
    
        self.progress_dialog.show() 
        self.set_all_buttons_enabled(False)
        
    # 调用百度API获得单词对应的语音文件，存入本地
        audio_map = await self.initialize_voice_pack("zh")

    # 调用爬虫程序从汉典(http网址)中爬取definition，存入.txt
        defin_map = await self.initialize_word_property("Definition",
            v_func.text_to_definition, v_data.DEFINITION_ADDRESS, "无")
        
        await asyncio.sleep(0.01)
        
    # 调用GoogleTranslator翻译文本
        trans_map = await self.initialize_word_property("Translation",
            v_func.translate_text, v_data.TRANSLATION_ADDRESS, "N/A")
    
    # 建立SQLite数据库来统一存放这些初始化的单词 
        
        parameters_for_SQLite = {
            "audio" : audio_map, 
            "definition" : defin_map, 
            "translation" : trans_map,
            "picture" : {word : None for word in v_data.Initial_Word_list}
        }
        
        try:    await v_func.update_database( address = v_data.WORD_BANK_ADDRESS, 
                    parameters_dict = parameters_for_SQLite, type_name = "word_bank")
        except Exception as error:  print(f"Error occurs when storing .db: {error}")
        
        self.set_all_buttons_enabled(True)
        self.progress_dialog.close()
        
    
    @asyncSlot()
    async def initialize_voice_pack(self, language = str()):
        
        audio_address_map = dict()
        progress_keeper = {"done" : 0 , "total" : len(v_data.Initial_Word_list)}
        
        if v_func.check_data_exist():
            print("Audio database is already downloaded!")
            
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
                return {None for word in v_data.Initial_Word_list}
            
            # Set sveral different tasks simultaneously to enhance effiency:
            
            file_lock = asyncio.Lock()
            simulation_module = asyncio.Semaphore(SIMUL_BOUND_VOICE)
            async def simul_task(word, language):
                async with simulation_module:
        # 为了适应百度API的魔鬼限速————设置random抖动式限速，提高通过率
                    await asyncio.sleep(random.uniform(0.1, 0.3)) 
                    try:
                        judge_res = await v_func.text_to_speech(request_agent,
                            token, text = word, lang = language, default_voice_mode = 1, 
                            filename = f"{word}_{language}.mp3", adjuster = file_lock)
                        if judge_res:   audio_address_map[word] = f"{word}_{language}.mp3"
                    except Exception as error:
                        print(f"Text_to_Voice Error: {word} has {error}")
                        audio_address_map[word] = None
                    finally:
                        progress_keeper["done"] += 1
                        QTimer.singleShot(0, lambda count = progress_keeper['done'] : 
                            self.update_progress_bar({ "done" : count,
                                "total" : progress_keeper["total"] }, "Audio"))
            
            # all_tasks = [ simul_task(current_word, language) 
            #         for current_word in v_data.Initial_Word_list ]
            # await asyncio.gather(*all_tasks)
            
        # 上面的写法尽管用来semaphore来限速，但是依旧在gather的一瞬间产生大量请求
            # 用分batch的形式来完善限速体系————调参来调速
            
            total_batches = math.ceil(len(v_data.Initial_Word_list))
            for i in range(total_batches):
                current_batch = v_data.Initial_Word_list[
                    i * SIMUL_BATCH_SIZE : (i + 1) * SIMUL_BATCH_SIZE]
                tasks = [simul_task(word , language) for word in current_batch]
                await asyncio.gather(*tasks, return_exceptions = True)
                await asyncio.sleep(INTERVAL_BETWEEN_BATCHES)  # 控制节奏，防止限速
        
        return audio_address_map
    
    # Definition和Translation的获取方式尽管在路径上存在差异（爬虫/隐式API）
        # 他们的时间表现形式大致相同，于是合成为一个函数
        
    @asyncSlot()
    async def initialize_word_property(self, property_name = str(),
        fetch_function : Optional[Callable] = None, save_address = str(), blank_default = str()):
        
        result_map = dict()
        progress_keeper = {"done": 0, "total": len(v_data.Initial_Word_list)}

        # 预加载已有数据，根据.db检测！
        if v_func.check_data_exist():
            print("Property database is already downloaded!")
            v_func.preload_existing_data(result_map, save_address)
            return result_map

        async with aiohttp.ClientSession(headers = v_data.REQUEST_HEADERS) as session:

            semaphore = asyncio.Semaphore(SIMUL_BOUND_DEFINITION)

            async def simul_task(word):
                # 按照输入情况选择合适的调取函数，以哈希表形式存储！
                async with semaphore:
                    try:
                        property = (await fetch_function(session, word) 
                            if property_name == "Definition" else await fetch_function(word))
                        result_map[word] = property if property else blank_default
                    except Exception as error:
                        print(f"Text_to_{property_name} Error: {word} has {error}")
                        result_map[word] = blank_default
                    finally:
                        progress_keeper["done"] += 1
                        QTimer.singleShot(0, lambda count = progress_keeper['done'] : 
                            self.update_progress_bar({ "done" : count,
                                "total" : progress_keeper["total"] }, property_name))

            # 无明显限速限制，于是取all_tasks即可！
            all_tasks = [simul_task(word) for word in v_data.Initial_Word_list]
            await asyncio.gather(*all_tasks, return_exceptions = True)

            v_func.save_loaded_data(result_map, save_address)

        return result_map
                
                
    def update_progress_bar(self, counter, ongoing = str()):
        percentage = int((counter["done"] / counter["total"]) * 100)
        if self.progress_dialog:
            self.progress_dialog.update_progress(percent = percentage, trait = ongoing)
        
    
    def on_Test_button_clicked():
        pass
    
    def on_Search_button_clicked():
        pass
    
    def on_Brochure_button_clicked():
        pass
    
    def on_Exit_button_clicked(self):
        reply = QMessageBox.question(
            self,
            title = "Confirmation",
            text = "Be sure that you've saved your Data for further use!",
            buttons = QMessageBox.Yes | QMessageBox.No,
            defaultButton = QMessageBox.No
        )
        if reply == QMessageBox.Yes:    
            self.Upper_parent.show_float_pet()
            self.close()
            
    def on_Mode_button_clicked():
        pass
    
    def show_self(self):   self.show()
    
    def set_all_buttons_enabled(self, enabled: bool):        
        for btn in self.findChildren(QPushButton):    btn.setEnabled(enabled)
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            title = "Confirmation",
            text = "Be sure that you've saved your Data for further use!",
            buttons = QMessageBox.Yes | QMessageBox.No,
            defaultButton = QMessageBox.No
        )
        if reply == QMessageBox.Yes:    
            self.Upper_parent.show_float_pet()
            event.accept()
        else:   event.ignore()
        

class Test_Widget(QWidget,Ui_Test_Window):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags()):
        super().__init__()
        self.setupUi(self)  
        self.Upper_parent = parent   
        self.result_display = None
        
        self.questions = {}
        self.current_idx = 0
        self.buttons = []   # 装载buttons
        
        self.correct_count = 0
    
    def on_Play_current_button_clicked():
        pass
    
    def on_Add_button_clicked():
        pass
    
    def on_Pause_button_clicked():
        pass
    
    def on_answer_button_clicked(self):
        current_click = self.sender()
        
        if self.current_idx > len(self.question):
            self.set_all_buttons_enabled(False)
            if not self.result_display:    
                self.result_display = Finish_Test_Widget(
                    parent = self, result = self.correct_count )
            self.result_display.show()
            
        else:
            pass
        
        # update_Progress来更新进度条
    
    def choose_mode(self):
        mode_selection = [
            "Random word-bank",
            "Selected words",   # 用于特殊装载, 留接口可以用
            "Words from my Brochure"
        ]
        current_mode, jdg = QInputDialog.getitem(self, "Initializing......", 
            "Please choose your preferred mode.", mode_selection, 0, False )
        if not jdg or not current_mode:     
            self.Upper_parent.show_self()
            self.close()
    
        self.initialize(mode = current_mode)# 根据不同模式加载不同体量的词库，并且随机选择choices，存入questions
        
        # 初始化
        
    def set_all_buttons_enabled(self, enabled: bool):        
        for btn in self.findChildren(QPushButton):    btn.setEnabled(enabled)
    
    def closeEvent(self, event):
        
        # Remember to eliminate the generated temp_data_storage
        
        self.Upper_parent.show_self()
        event.accept()
        
     
class Finish_Test_Widget(QWidget,Ui_Finish_Test):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags(), result = int()):
        super().__init__()
        self.setupUi(self)  
        self.Upper_parent = parent   
      
        self.Test_result      
      
    def on_Save_button_clicked(self):
        self.close()
        pass
    
    def on_Abandon_button_clicked(self):
        self.close()
        pass
    
    
    def closeEvent(self, event):
        
        # Remember to eliminate the generated temp_data_storage
        # Default is abandon
        
        self.Upper_parent.show_self()
        event.accept()

class Search_Widget(QWidget,Ui_Word_Search):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags()):
        super().__init__()
        self.setupUi(self)  
        self.Upper_parent = parent   
        
        self.Definition
        self.Translation
        
    def on_Search_word_button_clicked():
        pass
    
    def on_Play_button_clicked():
        pass
    
    def on_Add_button_clicked():
        pass
    
    def on_Back_button_clicked():
        pass
    
    
    def closeEvent(self, event):
        
        # Remember to eliminate the generated temp_data_storage
        
        self.Upper_parent.show_self()
        event.accept()
   
        
class Word_Bank_Widget(QWidget,Ui_My_Word_Brochure):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags()):
        super().__init__()
        self.setupUi(self)  
        self.Upper_parent = parent   
        
    def on_word_select_clicked():
        pass
    
    def on_Play_button_clicked():
        pass
    
    def on_Back_button_clicked():
        pass
    
    
    def closeEvent(self, event):
        
        # Remember to eliminate the generated temp_data_storage
        
        self.Upper_parent.show_self()
        event.accept()
        
