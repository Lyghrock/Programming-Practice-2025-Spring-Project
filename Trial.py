import asyncio
import aiohttp
import os
from reverse_function import get_voice_token, text_to_speech

async def test_text_to_speech():
    test_text = "操你妈"
    test_filename = "test_audio_output.mp3"

    async with aiohttp.ClientSession() as session:
        # Step 1: 获取 token
        token = await get_voice_token(session)
        if not token:
            print("[ERROR] 获取 token 失败。")
            return
        
        print(f"[INFO] 获取到 token：{token[:10]}...")

        # Step 2: 执行 TTS 合成
        await text_to_speech(
            session=session,
            token=token,
            text=test_text,
            lang="zh",
            default_voice_mode=0,
            filename=test_filename
        )

        # Step 3: 检查文件是否生成
        audio_path = os.path.join("D:\\Desk_Pet_Data_Storage\\Voice_Bank", test_filename)
        if os.path.exists(audio_path):
            print(f"[SUCCESS] 音频已成功保存：{audio_path}")
        else:
            print(f"[FAILURE] 音频文件未找到，请检查错误输出。")

if __name__ == "__main__":
    asyncio.run(test_text_to_speech())
