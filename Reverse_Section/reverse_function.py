import pydub.utils
import requests
    # 原本计划用request串发调用API，弃用，面对大量网络配置问题效率低下！
import sys
import os
import time
import asyncio
    # 异步请求模块———用于向API并发请求，与QtConcurrent相比加快了initialize速度
from pydub import AudioSegment
import pydub 

import sqlite3  # 用aiosqlite来代替sqlite3来实现异步写入.db数据库
import aiosqlite as SQL

import translate as ts
from bs4 import BeautifulSoup


from . import reverse_data_storage as v_data

INITIAL_SCALE = 5000
TEST_SCALE = 20

App_ID = "6951303"
voice_API = "GBhFPFtbTLZbU9r8C1rY45Hc"
voice_Secret_Key = "fuSEtZ9J1lhYuqepbmFBoeg0W3QQXVv8"

# Single word_to_audio request:

async def get_voice_token(session):

    # Get API token:
    API_url = f"https://aip.baidubce.com/oauth/2.0/token"
    parameters = {
        "grant_type": "client_credentials",
        "client_id": voice_API,
        "client_secret": voice_Secret_Key
    }
    async with session.get(API_url, params = parameters) as response:
        resp_json = await response.json()
        token = resp_json.get("access_token")
        return token
        # Need to judge if it's None!

# TTS part:

async def text_to_speech(session, token,
    text, lang = "zh", default_voice_mode = 0 
    ,filename = "Unknown_Vocabulary.mp3", adjuster = None ):

    # Input text and get the corresponding audio:
    Text_to_Speech_url = "https://tsn.baidu.com/text2audio"
    parameters_for_audio = {
        "tex": text,
            # Your target text to be converted into audio
        "tok": token,
            # API token for generating audio
        "cuid": "Daddy_needs_an_audio_for_my_text",    
            # Something like a username, give a random string and it's fine.
        "ctp": 1,   
            # DEFAULT SETTINGS CAN'T CHANGE !!!!!
            
    # Mutable parameters:
    
        "lan": lang,    # language: "zh","en"
        "spd": 3,       # speed:  ranging from 0 ~ 15
        "pit": 6,       # pitch:  ranging from 0 ~ 15
        "vol": 10,             # volume:  ranging from 0 ~ 15
        "per": default_voice_mode       # person:  for "en" choose only 0
            #  for "zh" has 0 (standard women), 1 (standard men), 3 (Emotional), 4 (Childish)
    }

    special_head = v_data.REQUEST_HEADERS.copy()
    special_head.update({'Content-Type': 'application/x-www-form-urlencoded'})
    
    os.makedirs(v_data.AUDIO_ADDRESS, exist_ok = True )
    file_address = os.path.join(v_data.AUDIO_ADDRESS , filename)
    audio_content = str()
    try:
        async with session.post(Text_to_Speech_url, 
            data = parameters_for_audio, headers = special_head) as target_audio:
            
            content_type = target_audio.headers.get("Content-Type","")
            if content_type == "audio/mp3":
                audio_content = await target_audio.read()
            else:
                error_for_tts = await target_audio.text()
                try:
                    with open(v_data.BLANK_AUDIO_ADDRESS,"rb") as f:
                        audio_content = f.read()
                except Exception as e:  print(f"{e}")
                print(f"Something went wrong: {error_for_tts}")
             
    # 用来保证再同一时刻只有一个协程在进行，否则出现协程任务池里reverse在写入前/中调用
        async with adjuster:   
            with open(file_address, "wb") as f:  
                f.write(audio_content)
                f.flush()   # 保证file是正常状态
                os.fsync(f.fileno())    
            
            print("start_to_reverse")
            if lang == "zh":   await reverse_audio(file_address)
            print("end_reversing")
    
            return True
                
    # Ensure Programme Safety!
    
    except Exception as error:
        print(f"Storage_error: {error}")
        return False

# TTS Assistent:

async def reverse_audio(audio_path):
    
    def single_reverse():
        # # 确保ffmpeg配置成功!
        # AudioSegment.converter = pydub.utils.which("ffmpeg")
        # AudioSegment.ffprobe = pydub.utils.which("ffprobe")
        
        try:
            audio = AudioSegment.from_file(audio_path, format = "mp3")
            reversed_audio = audio.reverse()
            os.remove(audio_path)
            reversed_audio.export(audio_path, format = "mp3")
        except Exception as error:  print(f"Error occurs:{error}")
    
    await asyncio.to_thread(single_reverse)
        
        
async def check_file_exist(file_path, timeout=5):
    def blocking_wait():
        start = time.time()
        while not os.path.exists(file_path):
            if time.time() - start > timeout:
                raise TimeoutError(f"Time Limit Exceeded when waiting file_writing:{file_path}")
            time.sleep(0.05)
    await asyncio.to_thread(blocking_wait)



# Programme Assistent:
def load_word_list(mode = "default"):
    
    tmp = list()
    judge_initial = not os.path.exists(v_data.WORD_BANK_ADDRESS)
    if not judge_initial:
        
        agent_for_SQLite = sqlite3.connect(v_data.WORD_BANK_ADDRESS)
        cursor = agent_for_SQLite.cursor()
        cursor.execute("SELECT word FROM word_bank")
        tmp = [row_tuple[0] for row_tuple in cursor.fetchall()]
        
        agent_for_SQLite.close()       
    else:
        try:
            address = v_data.INITIAL_ADDRESS if mode == "default" else v_data.TEST_ADDRESS
            scale = INITIAL_SCALE if mode == "default" else TEST_SCALE
            with open(address, "r", encoding="utf-8") as file:
                tmp = [line.strip() for line in file.readlines()[:scale]]
        except Exception as e:  print(f"Ewerror when first loading word list: {e}")
    return tmp
    
# def check_voice_directory():
    
#     if os.path.exists(v_data.AUDIO_ADDRESS) and os.path.isdir(v_data.AUDIO_ADDRESS):
#         # check if the corresponding folder exists
#         try:
#             with os.scandir(v_data.AUDIO_ADDRESS) as entries:
#                 file_count = sum(1 for entry in entries if entry.is_file() == True)
#             return file_count >= INITIAL_SCALE
#         except Exception as error:
#             print(f"Unable to access the target file: {error}")
#     else:   return False

   
# Crawler: 
    
async def text_to_definition(session, text):
    
    # Judge if it's a single character, which influences the crawling performance
    crawler_mode = "word"
    assert all('\u4e00' <= single_hanzi <= '\u9fff' 
        for single_hanzi in text), f"Your input is not purely Chinese."
    if len(text) == 1:  crawler_mode = "single character"
    
    text_url = f"https://www.zdic.net/hans/{text}"
        
    def_str = str()
    async with session.get(text_url) as hanzi_resp:
        if hanzi_resp.status != 200:
            print(f"Request to Crawl fails: {hanzi_resp.status}")
            return

        page_html_file = await hanzi_resp.text()
        soup = BeautifulSoup(page_html_file,"html.parser")
        
        definition_finder = soup.find("div", class_ ="dictionaries zdict")
        if definition_finder is None:
            print("Your word has no definition under current search environment.")
            return
        
        next_search = "content definitions"
        if crawler_mode == "single character":  next_search += " jnr"
        text_def = definition_finder.find("div", class_ = next_search)
        if crawler_mode == "word":  text_def = text_def.find("div", class_ = "jnr")
        
        if text_def:
            if crawler_mode == "single character":
                
                opt_definition = list()
                loc = text_def.find("ol")
                if not loc:   
                    print("Something went wrong and I 'can't find single definition")
                    return
                all_def_str = loc.find_all("li")
                max_count, count = 3, 0
                for curr in all_def_str:
                    if count >= max_count:   break
                    raw_text = curr.text.strip()
                    opt_definition.append(raw_text.split("：")[0])
                    count += 1
                    
            elif crawler_mode == "word":
                
                opt_definition = list()
                possible_location = text_def.find_all("p")
                # 遍历每个possible的条目，找含释义的部分
                for current in possible_location:
                    judge_cino = current.find("span", class_ = "cino")
                    judge_encs = current.find("span", class_ = "encs")
                    judge_wrong = current.find("span", class_ = "diczx1")
                    judge_wrong_2 = current.find("strong")
                    if judge_wrong or judge_wrong_2:   continue
                    if judge_encs:   judge_encs.extract()
                    if judge_cino:   judge_cino.extract()
                    target_text = current.text.strip().strip("∶")
                    opt_definition.append(target_text)
                # 如果至此为空，必然是不带拼音的sb词，故而直接取出
                if not opt_definition:  opt_definition.append(text_def.text.strip())
                
            def_str = ";".join(opt_definition)   
                    
        else:   
            print("Something went wrong and I 'can't find the definition.")
            return 
        
    return def_str
       
# Crawler Assistent:   

def check_data_exist():    return os.path.exists(v_data.WORD_BANK_ADDRESS)

def save_loaded_data(map = dict(), address = str()):
    
    folder = os.path.dirname(address)
    if not os.path.exists(folder):    os.makedirs(folder)
    try:
        with open(address, "w", encoding = "utf-8") as f:
            for word, definition in map.items():
                f.write(f"{word}\t{definition}\n")
    except Exception as error:  print(f"Save {address} Eror: {error}")
        
def preload_existing_data(map = dict(), address = str()):
    try:
        with open(address,"r",encoding = "utf-8") as f:
            for line in f.readlines():
                key, value = line.split("\t")[0],line.split('\t')[1]
                map[key] = value
    except Exception as e:  print(f"Load {address} Error: {e}")


# Translation Module:
import deep_translator as trl
TRANSLATOR = trl.GoogleTranslator(source = "zh-CN", target = "en")
async def translate_text(text):
    return await asyncio.to_thread(TRANSLATOR.translate, text)

        
# SQLite————WORD_BANK：

async def update_database(address = str() 
        ,parameters_dict = dict(), type_name = str()):
    
    dir_path = os.path.dirname(address)
    if dir_path and not os.path.exists(dir_path):    os.makedirs(dir_path)

    judge_initial = not os.path.exists(address)
    
    SQLite_lock = asyncio.Lock()
    async with SQLite_lock:
        
        async with SQL.connect(address) as agent:
            
            if judge_initial:
                await agent.execute(
                f"""
                    CREATE TABLE IF NOT EXISTS {type_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT NOT NULL UNIQUE,
                        translation TEXT,
                        definition TEXT,
                        audio TEXT,
                        picture TEXT,
                        enable_english_mark INTEGER
                    )
                """    )

            cursor = await agent.cursor()
            for trait, inserter in parameters_dict.items():
                
                current_data = [(key, inserter[key]) for key in inserter.keys()]
                    # print(current_data)
                    # print(type(current_data[0][1]))
                print(f"Trying to load {trait}.")
                await cursor.executemany(
                f'''
                    INSERT INTO {type_name} (word, {trait})
                    VALUES (?, ?)
                    ON CONFLICT(word) DO UPDATE SET {trait} = excluded.{trait}
                ''', current_data)
                
            await agent.commit()
    
async def get_data_from_database(text, address = str(), type_name = str()):
    
    try:    assert os.path.exists(address) == True
    except Exception as error:   
        print(f"Database do not exist. Itemgetter is invalid: {error}")
        return None
    
    async with SQL.connect(address) as agent:
        agent.row_factory = sqlite3.Row  # 返回哈希表
        cursor = await agent.execute(f"SELECT * FROM {type_name} WHERE word = ?",(text,))
        
        res = await cursor.fetchone()
        
        await cursor.close()
        
        return dict(res) if res else None
    

    
def initialize_data(mode = None):
    pass

    
