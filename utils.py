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
    
    (minutes, seconds) = str.split(':')
    return int(minutes) * 60 + float(seconds)

def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f'{minutes:02}:{seconds:04.1f}'

#ai_client = openai.OpenAI()

ai_client = openai.OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

#from google import genai

#ai_client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

def request_ai(prompt, frames=None):
    print("AI request:", prompt)

    messages = [{ "role": "user", "content": [ {"type": "text", "text": prompt} ] } ]
    if frames:
        for i, frame in enumerate(frames):
            buffered = BytesIO()
            frame.save(buffered, format="JPEG")
            base64_frame = base64.b64encode(buffered.getvalue()).hex()
            messages[0]["content"].append({"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_frame}"})

    if frames:
        for i, frame in enumerate(frames):
            messages.append({
                "role": "system",
                "content": f"frame {i}",
                "image": frame,
            })

    response = ai_client.chat.completions.create(
        model="qwen-turbo",
        temperature=0.9,
        max_tokens=100,
        messages=messages,
    )

    text = response.choices[0].message.content
    print("AI response:", text)
    return text