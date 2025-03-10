import time
import os
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer

VOICE_DIR = 'voices'
dashscope.api_key=os.getenv("DASHSCOPE_API_KEY")

class Voicer:
    def __init__(self, match):
        self.match = match

    def make_voice(self):
        for comment in self.match.comments:
            self._make_voice(comment)
            time.sleep(1)

    def _make_voice(self, comment):
        # skip if voice already exists
        voice_path = os.path.join(VOICE_DIR, f'{comment.time}.mp3')
        if os.path.exists(voice_path):
            return

        if not os.path.exists(VOICE_DIR):
            os.mkdir(VOICE_DIR)

        # generate and save voice
        synthesizer = SpeechSynthesizer(model="cosyvoice-v1", voice="longshuo")
        audio = synthesizer.call(comment.text)
        with open(voice_path, 'wb') as f:
            f.write(audio)

    def get_voice(self, comment):
        return os.path.join(VOICE_DIR, f'{comment.time}.mp3')