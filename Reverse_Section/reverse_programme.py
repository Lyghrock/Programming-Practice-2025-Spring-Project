from . import reverse_data_storage as v_data
from . import reverse_function as v_func

import os
import re
import random
import math

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QTextEdit, QLabel, 
    QMessageBox, QInputDialog, QFileDialog,
)
from PyQt5.QtCore import (
    QTimer, Qt, QUrl
)
from PyQt5.QtGui import (
    QPixmap, QIcon
)
from PyQt5.QtMultimedia import (
    QMediaPlayer, QMediaContent
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
        print("Language")
        
        # 维护一个计数进度条类，动态更新下载进度————（控件由loadUi实现）
        self.progress_dialog = v_data.ProgressDialog(parent = self)
        self.set_all_buttons_enabled(False)
        
        v_data.Initial_Word_list = v_func.load_word_list()
        self.Test_button.clicked.connect(self.on_Test_button_clicked)
        self.Search_button.clicked.connect(self.on_Search_button_clicked)
        self.Brochure_button.clicked.connect(self.on_Brochure_button_clicked)
        self.Exit_button.clicked.connect(self.on_Exit_button_clicked)
        self.Mode_button.clicked.connect(self.on_Mode_button_clicked)
        
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
        
        parameters_for_init = {
            "audio" : audio_map, 
            "definition" : defin_map, 
            "translation" : trans_map,
            "picture" : {word : None for word in v_data.Initial_Word_list} , 
            "enable_english_mark" : {word : 0 for word in v_data.Initial_Word_list}
        }
        
        try:    await v_func.update_database( address = v_data.WORD_BANK_ADDRESS, 
                    parameters_dict = parameters_for_init, type_name = "word_bank")
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
        
    
    def on_Test_button_clicked(self):
        self.hide()
        self.set_all_buttons_enabled(False)
        self.Test_Widget = Test_Widget(parent = self)
        self.Test_Widget.show()
    
    def on_Search_button_clicked(self):
        self.hide()
        self.set_all_buttons_enabled(False)
        self.Search_Widget = Search_Widget(parent = self)
        self.Search_Widget.show()
    
    def on_Brochure_button_clicked(self):
        self.hide()
        self.set_all_buttons_enabled(False)
        self.Word_Brochure_Widget = Word_Bank_Widget(parent = self)
        self.Word_Brochure_Widget.show()
    
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
            
    def on_Mode_button_clicked(self):
        pass    # 模式转换接口，需要配合中英文逻辑
    
    def set_all_buttons_enabled(self, enabled: bool):        
        for btn in self.findChildren(QPushButton):    btn.setEnabled(enabled)
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Confirmation",   "Sure to exit? ",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
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
        self.pause_display = None
        import inspect
        for frame in inspect.stack():
            print(f"{frame.filename}:{frame.lineno} - {frame.function}")
        
        self.test_data_stroage = dict()
        self.questions = list()
        self.player = QMediaPlayer(self)
        
        self.correct_count = 0
        self.current_idx = 0
        self.test_display_mode = str()
        
        # 默认按钮在button_List里的顺序是A/B/C/D：
        self.option_button_list = list()
        for item in ['A','B','C','D']:
            current_button_name = item + "_button"
            current_button = self.findChild(QPushButton,current_button_name)
            current_button.clicked.connect(self.on_answer_button_clicked)
            self.option_button_list.append(current_button)
        self.Add_button.clicked.connect(self.on_Add_button_clicked)
        self.Play_current_button.clicked.connect(self.on_Play_current_button_clicked)
        self.Pause_button.clicked.connect(self.on_Pause_button_clicked)
        
        self.test_mode = self.choose_mode()
        self.test_display_mode = self.choose_display_mode()
        params_for_init = self.prepare_for_initialize_params(self.test_mode)
        if params_for_init is None:
            self.Upper_parent.show()
            self.set_all_buttons_enabled(False)
            self.close()    # 保证一定有数据才开始test
            return
    
        asyncio.create_task(self.initialize(*params_for_init))
    
        self.time_keeper_initialize()
        
    def update_current_time(self):
        self.sec_count += 1
        if self.sec_count >= 60:
            self.min_count += 1
            self.sec_count = 0
        if self.min_count >= 60:
            self.result_display = (Finish_Test_Widget(parent = self, 
                result = "Time Limit Exceeded. You've failed the test." ) 
                if not self.result_display else self.result_display )
            self.set_all_buttons_enabled(False)
            self.result_display.show()
            
        self.Time_keeper.setText(f"{self.min_count:0>2}:{self.sec_count:0>2}")
        
    def update_button_content(self):
        
        for i in range(4):
            button = self.option_button_list[i]
            if self.test_display_mode == "picture":
                
                pixmap = QPixmap(self.questions[self.current_idx][1][i]["picture"])
                scaled_pixmap = pixmap.scaled(
                    size = self.button.size(),
                    aspectRatioMode = Qt.KeepAspectRatio,
                    transformMode = Qt.SmoothTransformation
                )
                
                self.button.setIcon(QIcon(scaled_pixmap))
                self.button.setIconSize(scaled_pixmap.size())  
            
            else:    button.setText(self.questions[self.current_idx][1][i][self.test_display_mode])
    
    def on_Play_current_button_clicked(self):
        audio_path = self.test_data_stroage[self.questions[self.current_idx][0]]["audio"]
        audio_url = QUrl.fromLocalFile(audio_path)
        audio_content = QMediaContent(audio_url)   
        self.player.setMedia(audio_content)
        self.player.setVolume(80) 
        self.player.play()
    
    def on_Add_button_clicked(self):
        pass
    
    def on_Pause_button_clicked(self):
        
        self.set_all_buttons_enabled(False)
        self.timer.stop()   # Timer停止计时
        self.pause_display = (Finish_Test_Widget(parent = self) 
                    if not self.pause_display else self.pause_display)
        self.pause_display.show()
    
    def on_answer_button_clicked(self):
        
        current_click = self.sender()
        # print(current_click.objectName())
        click_index = ord(current_click.objectName()[0]) - 65
        # print(click_index)
        
        correct_ans = self.questions[self.current_idx][0]
        current_ans = self.questions[self.current_idx][1][click_index]["word"]
        if correct_ans == current_ans:  self.correct_count += 1
        self.current_idx += 1 
        
        if self.current_idx == len(self.question):
            self.set_all_buttons_enabled(False)
            if not self.result_display:    
                self.result_display = Finish_Test_Widget(parent = self, 
                    result = f"You've answered {self.correct_count} correctly \
out of {len(self.questions)} with a time of {self.min_count:0>2}:{self.sec_count:0>2}" )
            self.result_display.show()
            
        else:    # update_Progress来更新进度条
            proportion = math.floor( 100 * self.current_idx / len(self.questions))
            self.Test_Progress.setValue(proportion)
            self.update_button_content()
    
    def choose_mode(self):
        
        print("choose mode here!")
        
        mode_selection = [
            "Random word-bank",
            "Selected words",   # 用于特殊装载, 留接口可以用
            "Words from my Brochure"
        ]
        current_mode, _ = QInputDialog.getItem(self, "Initializing......", 
            "Please choose your preferred mode.", mode_selection, 0, False )
        if not _ or not current_mode:     
            self.Upper_parent.show()
            self.close()
            
        return current_mode
    
    def choose_display_mode(self):
        # 初始化按钮和test的选择模式：
        current_display_mode, _2 = QInputDialog.getItem(self, "Choosing Test Icon...",
            "Please choose your preferred traits for test.", 
            ["definition", "translation", "word", "picture"], 0, False)
        if not _2 or not current_display_mode:     
            self.Upper_parent.show()
            self.close()

        return current_display_mode
    
    def prepare_for_initialize_params(self, mode = None):
        
        assert mode, "Please select a mode first."
        total_l = len(v_data.Initial_Word_list)
        
        if mode == "Random word-bank":
            
            # 输入一个合理的random size: 
            jdg, jdg_count = False, 0
            while jdg_count < 3:
                size, jdg = QInputDialog.getInt(self, "Random Slicing Size"
                    , "Please input a size for your upcoming test.", 
                    min = 20, max = math.floor(total_l/4))
                jdg_count += 1
                if jdg:   break
            else:   
                print("Fail to initialize my random word bank.")
                return None
            
            slicing = random.sample(range(0,total_l),size)
            test_key = v_data.Initial_Word_list
            test_address = v_data.WORD_BANK_ADDRESS
            
        elif mode == "Selected words":
            # NOTICE: 此处并非任何.db文件都可以被load，将检测其是否具有我的.db形式
            
            jdg_count = False
            while jdg_count < 3:
                # QFileDialog来选择自定义.db文件，检测是否正常获取
                test_address, _ = QFileDialog.getOpenFileName(self, "Please Choose your word bank",
                        "", "Database Files (*.db);;All Files (*)"  )
                jdg_count += 1
                test_key = v_func.check_data_validity(test_address)
                if test_key:    break
                else:    QMessageBox.warning(self, "Error", "Please select a valid .db file with correct format.")
            else:   
                print("Fail to get a valid path.")
                return None
            
            # 成功定位则按照正常流程提供中间变量
            size = v_func.get_data_size(address = test_address, type_name = "word_bank")
            slicing = list(range(0,size))
                    
        elif mode == "Words from my Brochure":
            test_key = v_func.check_data_validity(v_data.WORD_BROCHURE_ADDRESS)
            if test_key:
                test_address = v_data.WORD_BROCHURE_ADDRESS
                size = v_func.get_data_size(address = test_address, type_name = "word_bank")
                slicing = list(range(0,size))
            else:   
                print("Word Brochure Stroage is invalid, please check.")
                return None
    
        else:   raise Exception("It seems you didn't select mode correctly???")
        
        return slicing, test_key, test_address, size
             
    async def initialize(self, *params):
        
        mode = self.test_mode
        slicing ,test_key ,test_address ,word_bank_size = params
        
        # 从.db里取出数据，写入data_storage
        assert slicing, "Invalid Slicing Initialzation. Programme Exit."
        random.shuffle(slicing)    
        for index in slicing:
            current_key = test_key[index]
            current_data = await v_func.get_data_from_database(current_key,
                address = test_address, type_name = "word_bank")
            self.test_data_stroage.setdefault(current_key, current_data)
            
        # random为每个问题生成4个answer装入question:
        for current in self.test_data_stroage.values():
            question_word = current["word"]
            options = [self.test_data_stroage[test_key[
                        random.choice(slicing)]] for i in range(3)]
            options.append(current)
            assert len(options) == 4, "Werid??? Length of options are invalid."
            random.shuffle(options)
            self.questions.append((question_word, options))
        
        assert self.questions and self.test_data_stroage, "Blank occurs when data loading."
        self.update_button_content()
    
    def time_keeper_initialize(self):
       
        self.timer = QTimer(self)
        self.sec_count = 0
        self.min_count = 0
        self.timer.timeout.connect(self.update_current_time)
        self.timer.start(1000)
    
    def set_all_buttons_enabled(self, enabled: bool):        
        for btn in self.findChildren(QPushButton):    btn.setEnabled(enabled)
        
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Confirmation",
            "Be sure that you want to Abandon the current Test!",
            QMessageBox.Yes | QMessageBox.No,   QMessageBox.No
        )
        # Remember to eliminate the generated temp_data_storage
        if reply ==  QMessageBox.Yes:
            self.Upper_parent.show()
            event.accept()
        
     
class Finish_Test_Widget(QWidget,Ui_Finish_Test):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags(), result = None):
        super().__init__()
        self.setupUi(self)  
        self.Upper_parent = parent   
      
        if result is None:  
                # 此时代表是由pause按键触发的断点
            self.Save_button.clicked.connect(self.on_Resume_button_clicked)
            self.Save_button.setText("Resume")
            self.Test_result.setText(f"The Test is paused at question{self.Upper_parent.current_idx}.")
        else:   
                # 此时代表是由游戏结束触发的保存逻辑
            self.Save_button.clicked.connect(self.on_Save_button_clicked)
            self.Test_result.setText(result)
            
        self.Abandon_button.clicked.connect(self.on_Abandon_button_clicked)  
      
    def on_Resume_button_clicked(self):
        
        self.Upper_parent.timer.start(1000)
        self.Upper_parent.set_all_buttons_enabled(True)
        self.Upper_parent.show()
        self.close()
      
    @asyncSlot()
    async def on_Save_button_clicked(self):
        
        jdg_count = 0
        while jdg_count < 10:
            file_name, _ = QInputDialog.getText(self, 
                "Storing savings...","Please give your test a name.")
            if not _:   
                QMessageBox.warning(self,"Warning", "Empty input? Please Try Again!")
            elif len(file_name) > 15:   
                QMessageBox.warning(self, "Warning", 
                    "Input Too Long! Please rephrase it within 15 characters.")
            elif re.search(r'[\\/:*?"<>|]', file_name):
                QMessageBox.warning(self, "Warning", "Invalid characters in filename!")
            else:   
                real_file_name = (f"Name_{file_name}."
                                f"Mode_{self.Upper_parent.test_display_mode}."
                                f"Score_{int(self.Upper_parent.correct_count 
                                    / len(self.Upper_parent.questions) * 100):.2f}."
                                f"Duration_{self.Upper_parent.min_count:0>2}_"
                                    f"{self.Upper_parent.sec_count:0>2}.db")

                current_path = os.path.join(v_data.TEST_RESULT_ADDRESS,real_file_name)
                if os.path.exists(current_path) and os.path.isfile(current_path):
                    QMessageBox.warning(self,"Warning", "Repeated Name! Please change it!")
                else:    break
        else:   raise Exception("Too Many Trials for File Savings. Check the situation please.")
            
        parameters_for_save_test = {
            "audio" : dict(),
            "definition" : dict(),
            "translation" : dict(),
            "picture" : dict(),
            "enable_english_mark": dict()
        }
        for word in self.Upper_parent.test_data_storage.keys():
            for key in parameters_for_save_test.keys():
                parameters_for_save_test[key].setdefault(
                    word, self.Upper_parent.test_data_storage[word][key])
                
        try:  await v_func.update_database( address = current_path,
                  parameters_dict = parameters_for_save_test, type_name = "word_bank")
        except Exception as error:  print(f"Error occurs when storing .db: {error}")

        self.Upper_parent.Upper_parent.show()
        self.Upper_parent.close()
        self.close()
    
    def on_Abandon_button_clicked(self):
        
        reply = QMessageBox.question(
            self,   "Confirmation",
            "Be sure that you want to Abandon the current Test!",
            QMessageBox.Yes | QMessageBox.No,    QMessageBox.No
        )
        if reply == QMessageBox.Yes:    
            self.Upper_parent.Upper_parent.show()
            self.Upper_parent.close()
            self.close()
    
    
    def closeEvent(self, event):
        
        self.Upper_parent.timer.start(1000)
        self.Upper_parent.set_all_buttons_enabled(True)
        self.Upper_parent.show()
        event.accept()

class Search_Widget(QWidget,Ui_Word_Search):
    
    def __init__(self, parent = None, flags = Qt.WindowFlags()):
        super().__init__()
        self.setupUi(self)  
        self.Upper_parent = parent   
        
        self.Definition
        self.Translation
        
    def on_Search_word_button_clicked(self):
        pass
    
    def on_Play_button_clicked(self):
        pass
    
    def on_Add_button_clicked(self):
        pass
    
    def on_Back_button_clicked(self):
        pass
    
    
    def closeEvent(self, event):
        
        # Remember to eliminate the generated temp_data_storage
        
        self.Upper_parent.show()
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
        
        self.Upper_parent.show()
        event.accept()
        
