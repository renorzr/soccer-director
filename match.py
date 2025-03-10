from utils import parse_time
from team import Team
from event import Event
from scoreboard import Scoreboard

# Description: This file contains the Match class which is used to store the match data.
class Match:
    def __init__(self, obj):
        self.name = obj['name']
        self.teams = [Team(obj['name'], obj['color'], obj.get('code'), obj.get('score', 0)) for obj in obj['teams']]
        self.main_video = obj['main_video']
        self.logo = obj.get('logo', 'logo.png')
        self.start = parse_time(obj.get('start', 0))
        self.end = parse_time(obj.get('end'))
        self.bias = obj.get('bias', 0.2)
        self.quarter = obj.get('quarter')
        self.intro = obj.get('intro')
        self.narrator = obj.get('narrator', '云说')
        self.events = []
        self.comments = []
        self.manual_events = obj.get('events', [])
        self.score_updates = []
        self.scoreboard = Scoreboard.from_dict(self.name, self.teams[0].code, self.teams[1].code, obj['scoreboard']) if 'scoreboard' in obj else None

    def update_score(self, time, team, score):
        if team is not None:
            self.teams[team].score = score
        self.score_updates.append(ScoreUpdate(time, self.teams[0].score, self.teams[1].score))

class ScoreUpdate:
    def __init__(self, time, score0, score1):
        self.time = time
        self.score0 = score0
        self.score1 = score1

    def __repr__(self):
        return f"time: {self.time}, score0: {self.score0}, score1: {self.score1}"
