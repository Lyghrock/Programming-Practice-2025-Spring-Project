import requests
    # 原本计划用request串发调用API，弃用，面对大量网络配置问题效率低下！
import sys
import os
    # 异步请求模块———用于向API并发请求，与QtConcurrent相比加快了initialize速度
from pydub import AudioSegment


import reverse_data_storage as v_data



App_ID = "6951303"
voice_API = "GBhFPFtbTLZbU9r8C1rY45Hc"
voice_Secret_Key = "fuSEtZ9J1lhYuqepbmFBoeg0W3QQXVv8"

# Single word_to_audio request:

async def get_token(session):

    # Get API token:
    
    API_url = f"https://aip.baidubce.com/oauth/2.0/token"
    parameters = {
        "grant_type": "client_credentials",
        "client_id": voice_API,
        "client_secret": voice_Secret_Key
    }
    async with session.get(API_url, params = parameters) as response:
        token = response.json().get("access_token")
        return token
        # Need to judge if it's None!

async def text_to_speech(seesion, token,
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
        "spd": 5,       # speed:  ranging from 0 ~ 15
        "pit": 5,       # pitch:  ranging from 0 ~ 15
        "vol": 5,       # volume:  ranging from 0 ~ 15
        "per": default_voice_mode       # person:  for "en" choose only 0
            #  for "zh" has 0 (standard women), 1 (standard men), 3 (Emotional), 4 (Childish)
    }

    head = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        async with seesion.post(Text_to_Speech_url, 
            data = parameters_for_audio, headers = head) as target_audio:
            
            file_address = "D:\\Desk_Pet_Data_Storage\\Voice_Bank"
            os.makedirs(file_address, exist_ok = True )
            file_address = os.path.join(file_address , filename)
            
            content_type =target_audio.headers.get("Content-Type","")
            if content_type == "audio/mp3":
                audio_content = await target_audio.read()
                with open(file_address, "wb") as f:  f.write(audio_content)
                if lang == "zh":    reverse_audio(file_address)
            else:
                error_for_tts = await target_audio.text()
                print(f"Something went wrong: {error_for_tts}")
    except Exception as error:
        print(f"Storage_error: {error}")

def get_initial_word_bank():
    pass

def reverse_audio(audio_path):
    audio = AudioSegment.from_mp3(audio_path)
    reversed_audio = audio.reverse()
    reverse_audio.export(audio_path, format = "mp3")
    
    
    