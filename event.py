import yaml
import os
from utils import format_time


class Event:
    def __init__(self, type, start, end, team=None, player=None, desc=None):
        self.id = f'{start}-{type}'
        self.level = level_of(type)
        self.type = type
        self.start = start
        self.end = end
        self.team = team
        self.player = player
        self.desc = desc
    
    @classmethod
    def from_dict(cls, obj):
        return cls(obj['type'], obj['start'], obj['end'], obj.get('team'), obj.get('player'), obj.get('desc'))

    @classmethod
    def load_from_yaml(cls, file_path):
        if not os.path.exists('events.yaml'):
            return []

        with open(file_path, 'r') as f:
            data = yaml.safe_load(f) or []

        return [Event.from_dict(obj) for obj in data]

    @classmethod
    def save_to_yaml(cls, file_path, events):
        with open(file_path, 'w') as f:
            yaml.dump([e.__dict__ for e in events], f)

    @property
    def duration(self):
        return self.end - self.start

    def __repr__(self):
        return f'id: {self.id}, level: {self.level}, type: {self.type}, start: {format_time(self.start)}, end: {format_time(self.end)}, team: {self.team}, desc: {self.desc}'

EVENT_LEVELS = {
    'goal': 10,
    'miss': 9,
    'foul': 8,
    'save': 7,
    'pass': 5,
    'start': 7,
    'end': 7,
    'comment': 6,
}

def level_of(event_type):
    return EVENT_LEVELS.get(event_type, 0) 

