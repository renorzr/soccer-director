import yaml
import os
from utils import format_time, parse_time
import csv
import random
import string
from enum import Enum

    
class Tag(Enum):
    Replay = 1,
    Deadball = 2,
    Liveball = 3,


class EventType(Enum):
    Start = 6, [Tag.Liveball], "比赛开始", "简短宣布比赛开始"
    End = 7, [Tag.Deadball], "比赛结束", "如果不是最后一节(第4节)，首先宣布一节比赛结束（如：第x节比赛结束；比赛告一段落；裁判吹响了第x节比赛结束的哨声；等等），然后补充比赛结果和点评，最后提醒观众下一节比赛稍后开始。如果是最后一节，宣布比赛结束（如：终场哨响；全场比赛结束；裁判员吹响了终场哨；比赛结束；等等。），然后补充比赛结果和点评，最后感谢观众收看。"
    Goal = 9, [Tag.Replay, Tag.Deadball], "进球", "简短，以\"球进啦！\"、\"进了！\"、\"好球！\"等开头"
    Miss = 8, [Tag.Replay], "射门未进", "简短，以\"哎呀没进！\"、\"打偏了！\"、\"可惜！\"等开头"
    Foul = 8, [Tag.Replay, Tag.Deadball], "犯规", "简短，以\"这个球是犯规\"、\"裁判吹哨了！\"、\"犯规！\"等开头"
    Out = 5, [Tag.Deadball], "出界", None
    Continue = 5, [Tag.Liveball], "比赛继续", None
    Breakthrough = 6, [], "突破", None
    Save = 7, [], "扑救", None
    Kickoff = 7, [Tag.Liveball], "开球", None
    Tackle = 6, [], "抢断", None
    Pass = 5, [], "传球", None
    Comment = 8, [], "解说", "原样输出"
    Other = 7, [], "其它事件", "根据事件描述，简短解说。"

    def __init__(self, level, default_tags, event_name, req):
        self.level = level
        self.default_tags = default_tags
        self.event_name = event_name
        self.req = req


class Event:
    HEADERS = ['id', 'time', 'type', 'team', 'player', 'tags', 'desc']

    def __init__(self, id, type, time, team=None, player=None, desc=None, tags=None):
        self.type = type
        self.time = parse_time(time)
        self.team = int(team) if team else None
        self.player = player
        self.desc = desc
        self.tags = tags
        self.id = id or f"{type.name}_{team}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"

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
    def save_to_csv(cls, file_path, events):
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(cls.HEADERS)
            writer.writerows([e.to_row() for e in events])

    def to_row(self):
        a_dict = self.__dict__.copy()
        a_dict['type'] = a_dict['type'].name
        a_dict['time'] = format_time(a_dict['time'])
        a_dict['tags'] = ','.join([t.name for t in a_dict['tags']])
        return [a_dict[header] for header in Event.HEADERS] 
    
    @classmethod
    def from_dict(cls, obj):
        tag_str = obj.get('tags') or ''
        tags = [Tag[s] for s in tag_str.split(',')] if tag_str else []
        return cls(obj.get('id'), EventType[obj['type']], obj['time'], obj.get('team'), obj.get('player'), obj.get('desc'), tags)

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

    def __repr__(self):
        return f'id: {self.id}, type: {self.type}, time: {format_time(self.time)}, team: {self.team}, player: {self.player}, desc: {self.desc}, tags: {self.tags}'
