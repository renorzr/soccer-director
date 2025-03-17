import openai
import os
from io import BytesIO
import base64

# Description: Utility functions for the project

# Description: This function parses a time string in the format 'mm:ss.s' to seconds.
def parse_time(value):
    # if value is already a number, return it
    if value is None or isinstance(value, (int, float)):
        return value
    
    (minutes, seconds) = str(value).split(':')
    return int(minutes) * 60 + float(seconds)


def format_time(seconds, decimal_places=1, use_separator=True):
    minutes = int(seconds // 60)
    seconds = seconds % 60
    
    sep = ':' if use_separator else ''
    if decimal_places == 0:
        return f'{minutes:02d}{sep}{seconds:02.0f}'
    
    dot = '.' if use_separator else ''
    width = decimal_places + 3  # 3 = 2 (整数位) + 1 (小数点)
    return f'{minutes:02d}{sep}{seconds:0{width}.{decimal_places}f}'.replace('.', dot)


ai_client = openai.OpenAI()

#ai_client = openai.OpenAI(
#    api_key=os.getenv("DASHSCOPE_API_KEY"),
#    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#)

#from google import genai

#ai_client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

def request_ai(prompt, frames=None):
    print("AI request:", prompt)
    content = [ {"type": "text", "text": prompt} ]

    if frames:
        #videos = []
        #content.append({"type": "video", "video": videos})

        for i, frame in enumerate(frames):
            buffered = BytesIO()
            frame.save(buffered, format="JPEG")
            base64_frame = base64.b64encode(buffered.getvalue()).decode("utf-8")
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_frame}"}})
            #videos.append(f"data:image/jpeg;base64,{base64_frame}")

    response = ai_client.chat.completions.create(
        #model="qwen-vl-max-latest",
        model="gpt-4o-mini",
        temperature=0.9,
        max_tokens=100,
        messages=[{ "role": "user", "content": content } ],
    )

    text = response.choices[0].message.content
    print("AI response:", text)
    return text

class ChatAI:
    def __init__(self, model="gpt-4o-mini"):
        self.model = model
        self.messages = []

    def chat(self, prompt):
        print("chat:", prompt)
        self.messages.append({"role": "user", "content": prompt})
        response = ai_client.chat.completions.create(
            model=self.model,
            messages=self.messages,
        )
        self.messages.append({"role": "assistant", "content": response.choices[0].message.content})
        result = response.choices[0].message.content
        print("chat result:", result)
        return result
