import time
import os
import dashscope
import hashlib
from fish_audio_sdk import Session, TTSRequest, Prosody

VOICE_DIR = 'voices'
dashscope.api_key=os.getenv("DASHSCOPE_API_KEY")
session = Session(os.getenv('FISH_AUDIO_API_KEY'))

class Voicer:
    def __init__(self, match):
        self.match = match

    def make_voice(self):
        for comment in self.match.comments:
            self.make_text_voice(comment.text)

    def make_text_voice(self, text):
        if not text:
            return

        # skip if voice already exists
        voice_path = self.get_voice(text)
        print(f"make voice for {text} at {voice_path}")
        if os.path.exists(voice_path) and os.path.getsize(voice_path) > 0:
            print(f"voice already exists for {text} at {voice_path}")
            return voice_path

        if not os.path.exists(VOICE_DIR):
            os.mkdir(VOICE_DIR)

        # generate and save voice
        print(f"generating voice for comment {text} with path {voice_path}")
        with open(voice_path, 'wb') as f:
            for chunk in session.tts(TTSRequest(
                reference_id=os.getenv('FISH_AUDIO_MODEL'),
                text=text
            )):
                f.write(chunk)
        time.sleep(1)

        return voice_path

    def get_voice(self, text):
        return os.path.join(VOICE_DIR, self.voice_name(text))

    def voice_name(self, text):
        return f"{hashlib.md5(text.encode('utf-8')).hexdigest()}.mp3" if text else None

