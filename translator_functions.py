from PIL import Image
import pytesseract
import os
from openai import OpenAI


# 设置 pytesseract 使用的临时文件夹为一个干净的英文路径
os.environ["TMP"] = "D:\\Temp"
os.environ["TEMP"] = "D:\\Temp"

# 如果这个路径不存在，先创建
if not os.path.exists("D:\\Temp"):
    os.makedirs("D:\\Temp")

pytesseract.pytesseract.tesseract_cmd = r"../Tesseract/tesseract.exe"


def extract_text_from_image(image_path: str):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="eng")  # 识别英文
        return text.strip()
    except Exception as e:
        return f"发生错误：{e}"


my_prompt = """
你将担任一个翻译官，对一段英语进行翻译
请尝试理解这段英语的内容，结合语境文意进行翻译
如果这段内容非常学术，请使用学术的方式翻译，使用正规的专有名词
由于给你的文段由图像识别产生，可能会包含一些混乱字符或错误单词，请从整体上把握文段的大意，并对可能的缺失部分进行推理与补全
可能需要抛弃一部分乱字符不翻译
"""

output_format ="""
输出必须有且仅有对原文段的中文翻译，要求语句流畅，语义明确
不要输出除了翻译之外的东西
"""


prompt = my_prompt+output_format
API_KEY = "sk-0fd83851c92841c2a7b5f96fffa4e3bd" 
model_name = "deepseek-chat"
client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

def get_translation(client: OpenAI, model_name: str, text: str):
    try:
        response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": f"Translate the following English text into Chinese:\n{text}"
            }
        ],
            stream=False,
            temperature=0
        )
        chinese = response.choices[0].message.content.strip()
        return chinese
    except Exception as e:
        print(f"翻译请求失败：{e}")
        return f"翻译请求失败：{e}"

def translate(image_path: str) -> str:  
    text = extract_text_from_image(image_path)
    chinese = get_translation(client,model_name,text)
    return chinese


# image_path = r"D:\\python\\Practice of programming\\Py_Qt\\5ac7c6d2a165a842b8afc6fd1a0bddd.jpg"
# text = extract_text_from_image(image_path)
# chinese = get_translation(client,model_name,text)
# print(chinese)