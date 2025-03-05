import os

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

        # generate voice
        # TODO: call text-to-speech API

    def get_voice(self, comment):
        return os.path.join(VOICE_DIR, f'{comment.time}.mp3')