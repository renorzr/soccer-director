import yaml
import os
from utils import format_time, parse_time
import csv

class Event:
    def __init__(self, type, start, end, team=None, player=None, desc=None):
        self.level = level_of(type)
        self.type = type
        self.start = parse_time(start)
        self.end = parse_time(end)
        self.team = int(team) if team else None
        self.player = player
        self.desc = desc
        self.id = f'{format_time(self.start, 1, False)}-{type}'

    @classmethod
    def load_from_csv(cls, file_path):
        print(f"loading events from {file_path}")
        if not os.path.exists(file_path):
            return []

        result = []
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)  # 读取表头
            for row in reader:
                # 将行数据转换为字典
                event_dict = {}
                for i, value in enumerate(row):
                    if value:  # 只添加非空值
                        event_dict[headers[i]] = value
                if 'type' in event_dict:
                    result.append(cls.from_dict(event_dict))

        print(f"loaded {len(result)} events")
        return result
    
    @classmethod
    def from_dict(cls, obj):
        print(obj)
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
    'kickoff': 5,
}

def level_of(event_type):
    return EVENT_LEVELS.get(event_type, 0) 

