import yaml
import os
from utils import format_time, parse_time
import csv
import random
import string
from enum import Enum

    
# 事件标签
class Tag(Enum):
    Replay = 1,   # 发生的事件需要重放
    Deadball = 2, # 比赛进入死球状态
    Liveball = 3, # 比赛进入活球状态

# 事件类型
class EventType(Enum):
    Start = 6, [Tag.Liveball], "比赛开始", "简短宣布比赛开始"
    End = 7, [Tag.Deadball], "比赛结束", "宣布全场比赛结束（如：终场哨响；全场比赛结束；裁判员吹响了终场哨；比赛结束；等等。），然后补充比赛结果，用两三句励志且富有诗意的表达点评比赛，最后感谢观众收看。"
    Goal = 9, [Tag.Replay, Tag.Deadball], "进球", "简短，以\"球进啦！\"、\"进啦！\"、\"好球！\"等开头"
    Miss = 8, [Tag.Replay], "射门未进", "简短，以\"哎呀没进！\"、\"打偏了！\"、\"可惜！\"等开头"
    Foul = 8, [Tag.Replay, Tag.Deadball], "犯规", "简短，以\"这个球是犯规\"、\"裁判吹哨了！\"、\"犯规！\"等开头"
    Out = 5, [Tag.Deadball], "出界", "简短"
    Continue = 5, [Tag.Liveball], "比赛继续", "简短"
    Breakthrough = 6, [], "突破", "简短"
    Save = 7, [], "扑救", "简短"
    Kickoff = 7, [Tag.Liveball], "开球", "简短，如：\"xx队开球了\""
    Tackle = 6, [], "抢断", "简短"
    Pass = 5, [], "传球", "简短"
    Comment = 8, [], "解说", "原样输出"
    Other = 7, [], "其它事件", "根据事件描述，简短解说。"

    def __init__(self, level, default_tags, event_name, req):
        self.level = level
        self.default_tags = default_tags
        self.event_name = event_name
        self.req = req


# 事件
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
        self.replay_time = None

    @classmethod
    def load_from_csv(cls, file_path):
        print(f"loading events from {file_path}")
        if not os.path.exists(file_path):
            return []

        result = []
        with open(file_path, 'r', encoding='utf-8') as f:
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
        with open(file_path, 'w', newline='', encoding="utf-8") as f:
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

    def __repr__(self):
        return f'id: {self.id}, type: {self.type}, time: {format_time(self.time)}, team: {self.team}, player: {self.player}, desc: {self.desc}, tags: {self.tags}'
