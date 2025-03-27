from utils import parse_time
from team import Team
from event import Event
from scoreboard import Scoreboard
import os
import yaml

# Description: This file contains the Game class which is used to store the game data.
class Game:
    def __init__(self, game_id, obj):
        self.game_id = game_id
        self.name = obj['name']
        self.start = 0
        self.end = None
        self.description = obj.get('description', '')
        self.teams = [Team(obj['name'], obj['color'], obj.get('code'), obj.get('score', 0)) for obj in obj['teams']]
        self.main_video = obj.get('main_video', f'{game_id}.mp4')
        self.logo_img = obj.get('logo_img', find_logo_img())
        self.logo_video = obj.get('logo_video', 'logo.mp4')
        self.bgm = obj.get('bgm', 'bgm.mp3')
        self.prev_time = parse_time(obj.get('prev_time', 0))
        self.bias = obj.get('bias', 0.2)
        self.quarter = obj.get('quarter')
        self.intro = obj.get('intro')
        self.narrator = obj.get('narrator', '云说')
        self.events = Event.load_from_csv(f'events.{game_id}.csv')
        self.comments = []
        self.score_updates = []
        self.deadballs = []

        with open(obj.get('scoreboard', 'scoreboard.yaml'), 'r') as f:
            scoreboard_props = yaml.safe_load(f)

        self.scoreboard = Scoreboard.from_dict(
            {'title': self.name, 'team0': self.teams[0].code, 'team1': self.teams[1].code, 'quarter': 'Q' + str(self.quarter)}, 
            scoreboard_props)

        self.score_updates.append(ScoreUpdate(self.start, self.teams[0].score, self.teams[1].score))

        self.load_start_and_end()

    def load_start_and_end(self):
        # find the first event with type 'start'
        for event in self.events:
            if event.type == 'start':
                self.start = event.start
                break
        # find the last event with type 'end'
        for event in self.events:
            if event.type == 'end':
                self.end = event.start

    def update_score(self, time, team=None, score=None):
        if team is not None:
            self.teams[team].score = score
        self.score_updates.append(ScoreUpdate(time, self.teams[0].score, self.teams[1].score))

    def game_time(self, time):
        return time - self.start + self.prev_time

class ScoreUpdate:
    def __init__(self, time, score0, score1):
        self.time = time
        self.score0 = score0
        self.score1 = score1

    def __repr__(self):
        return f"time: {self.time}, score0: {self.score0}, score1: {self.score1}"

def find_logo_img():
    exts = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'ico', 'webp']
    for ext in exts:
        path = f'logo.{ext}'
        if os.path.exists(path):
            return path
    return None
