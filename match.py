from utils import parse_time
from team import Team
from event import Event

# Description: This file contains the Match class which is used to store the match data.
class Match:
    def __init__(self, obj):
        self.name = obj['name']
        self.teams = [
            Team(obj['team1']['name'], obj['team1']['color']),
            Team(obj['team2']['name'], obj['team2']['color']),
        ]
        self.main_video = obj['main_video']
        self.logo_video = obj['logo_video']
        self.start = parse_time(obj.get('start', 0))
        self.end = parse_time(obj.get('end'))
        self.bias = obj.get('bias', 0.0)
        self.quarter = obj.get('quarter')
        self.intro = obj.get('intro')
        self.events = []
        self.comments = []
