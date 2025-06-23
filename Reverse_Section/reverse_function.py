import pydub.utils
import requests
    # 原本计划用request串发调用API，弃用，面对大量网络配置问题效率低下！
import sys
import os
import time
import deep_translator as trl
import asyncio
    # 异步请求模块———用于向API并发请求，与QtConcurrent相比加快了initialize速度
from pydub import AudioSegment
import pydub 

import sqlite3

import translate as ts
from bs4 import BeautifulSoup


import reverse_data_storage as v_data

INITIAL_SCALE = 5000

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
    ,filename = "Unknown_Vocabulary.mp3" ):

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
        "spd": 2,       # speed:  ranging from 0 ~ 15
        "pit": 5,       # pitch:  ranging from 0 ~ 15
        "vol": 5,       # volume:  ranging from 0 ~ 15
        "per": default_voice_mode       # person:  for "en" choose only 0
            #  for "zh" has 0 (standard women), 1 (standard men), 3 (Emotional), 4 (Childish)
    }

    special_head = v_data.REQUEST_HEADERS.copy()
    special_head.update({'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        async with session.post(Text_to_Speech_url, 
            data = parameters_for_audio, headers = special_head) as target_audio:
            
            os.makedirs(v_data.AUDIO_ADDRESS, exist_ok = True )
            file_address = os.path.join(v_data.AUDIO_ADDRESS , filename)
            
            # Store and then Reverse the audio
            
            content_type = target_audio.headers.get("Content-Type","")
            if content_type == "audio/mp3":
                audio_content = await target_audio.read()
            else:
                error_for_tts = await target_audio.text()
                with open(v_data.BLANK_AUDIO_ADDRESS,"rb") as f:
                    audio_content = f.read()
                print(f"Something went wrong: {error_for_tts}")
                
            with open(file_address, "wb") as f:  
                f.write(audio_content)
                f.flush()   # 保证file是正常状态
                os.fsync(f.fileno())    
                    
            await check_file_exist(file_address)
            if lang == "zh":   reverse_audio(file_address)
    
            return True
                
    # Ensure Programme Safety!
    
    except Exception as error:
        print(f"Storage_error: {error}")
        return False

# TTS Assistent:
async def check_file_exist(file_path, timeout=5):
    def blocking_wait():
        start = time.time()
        while not os.path.exists(file_path):
            if time.time() - start > timeout:
                raise TimeoutError(f"等待文件 {file_path} 超时")
            time.sleep(0.05)
    await asyncio.to_thread(blocking_wait)

def reverse_audio(audio_path):
    
    # # 确保ffmpeg配置成功!
    # AudioSegment.converter = pydub.utils.which("ffmpeg")
    # AudioSegment.ffprobe = pydub.utils.which("ffprobe")
    
    try:
        audio = AudioSegment.from_file(audio_path, format = "mp3")
        reversed_audio = audio.reverse()
        os.remove(audio_path)
        reversed_audio.export(audio_path, format = "mp3")
    except Exception as error:  print(f"Error occurs:{error}")
        


# Programme Assistent:
def load_word_list():
    
    tmp = list()
    
    judge_initial = not os.path.exists(v_data.WORD_BANK_ADDRESS)
    if not judge_initial:
        
        agent_for_SQLite = sqlite3.connect(v_data.WORD_BANK_ADDRESS)
        cursor = agent_for_SQLite.cursor()
        cursor.execute("SELECT word FROM word_bank")
        tmp = cursor.fetchall()
        
        agent_for_SQLite.commit()
        agent_for_SQLite.close()
        
    else:
        try:
            with open(v_data.INITIAL_ADDRESS, "r", encoding="utf-8") as file:
                tmp = [line.strip() for line in file.readlines()[:INITIAL_SCALE]]
        except Exception as e:  print(f"Error when first loading word list: {e}")
    return tmp
    
def check_voice_directory():
    
    if os.path.exists(v_data.AUDIO_ADDRESS) and os.path.isdir(v_data.AUDIO_ADDRESS):
        # check if the corresponding folder exists
        try:
            with os.scandir(v_data.AUDIO_ADDRESS) as entries:
                file_count = sum(1 for entry in entries if entry.is_file() == True)
            return file_count >= INITIAL_SCALE
        except Exception as error:
            print(f"Unable to access the target file: {error}")
    else:   return False

def check_data_exist():    return os.path.exists(v_data.WORD_BANK_ADDRESS)
    
   
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
def save_definition_data(definition_map = dict()):
    
    try:
        with open(v_data.DEFINITION_ADDRESS, "w", encoding = "utf-8") as f:
            for word, definition in definition_map.items():
                f.write(f"{word}\t{definition}\n")
    except Exception as error:  print(f"Save_def Eror: {error}")
        

# Translation Module:

def translate_text(text):   
    res = None
    try:    res = trl.GoogleTranslator(source = "auto", target = "en").translate(text)
    except Exception as error:  print(f"Translation Error: {error}")
    return res
      
        
# SQLite datatype:

def update_database(parameters_dict = dict()):

    judge_initial = not os.path.exists(v_data.WORD_BANK_ADDRESS)

    agent_for_SQLite = sqlite3.connect(v_data.WORD_BANK_ADDRESS)
    cursor = agent_for_SQLite.cursor()
    
    if judge_initial:
        cursor.execute(
    """
        CREATE TABLE IF NOT EXISTS word_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            translation TEXT,
            definition TEXT,
            audio TEXT,
            picture TEXT,
            enable_english_mark INTEGER
        )
    """
        )
    
    else:  pass
    
    for trait, inserter in parameters_dict.items():
        print(f"Trying to load {trait}.")
        cursor.executemany(
    f'''
        INSERT INTO word_bank (word, {trait})
        VALUES (?, ?)
        ON CONFLICT(word) DO UPDATE SET {trait} = excluded.{trait}
    ''', [(key, inserter[key]) for key in inserter.keys()])
        
    agent_for_SQLite.commit()
    agent_for_SQLite.close()