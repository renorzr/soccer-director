import os
import requests

VOICE_DIR = 'voices'

class Voicer:
    def __init__(self, match):
        self.match = match

    def make_voice(self):
        for comment in self.match.comments:
            self._make_voice(comment)

    def _make_voice(self, comment):
        # skip if voice already exists
        voice_path = os.path.join(VOICE_DIR, f'{comment.time}.mp3')
        if os.path.exists(voice_path):
            return

        if not os.path.exists(VOICE_DIR):
            os.mkdir(VOICE_DIR)

        # generate voice
        url = os.environ.get('CHATTTS_URL') + '/v1/audio/speech'
        response = requests.post(url, json={
            'model': 'chattts',
            'input': comment.text,
            'voice': '好哥们',
            'style': 'chat',
        })

        response.raise_for_status()

        with open(voice_path, 'wb') as f:
            f.write(response.content)

    def get_voice(self, comment):
        return os.path.join(VOICE_DIR, f'{comment.time}.mp3')