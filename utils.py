import openai
import os

# Description: Utility functions for the project

# Description: This function parses a time string in the format 'mm:ss.s' to seconds.
def parse_time(value):
    # if value is already a number, return it
    if value is None or isinstance(value, (int, float)):
        return value
    
    (minutes, seconds) = str.split(':')
    return int(minutes) * 60 + float(seconds)

def format_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f'{minutes:02}:{seconds:04.1f}'

#ai_client = openai.OpenAI()

#ai_client = openai.OpenAI(
#    api_key=os.getenv("DASHSCOPE_API_KEY"),
#    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#)

from google import genai

ai_client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
