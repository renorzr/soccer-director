import yaml
import os
from utils import format_time


class Event:
    def __init__(self, level, type, start, end, team=None, desc=None):
        self.id = f'{start}-{type}'
        self.level = level
        self.type = type
        self.start = start
        self.end = end
        self.team = team
        self.desc = desc
    
    @classmethod
    def from_dict(cls, obj):
        return cls(obj['level'], obj['type'], obj['start'], obj['end'], obj.get('team'), obj.get('desc'))

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