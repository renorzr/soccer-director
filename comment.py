import os
import yaml


class Comment:
    def __init__(self, time, text, type, event_id=None, event_level=0):
        self.time = time
        self.text = text
        self.type = type
        self.event_id = event_id
        self.event_level = event_level

    def __str__(self):
        return f'{self.time}: {self.text}'

    @classmethod
    def from_dict(cls, obj):
        return cls(obj['time'], obj['text'], obj['type'], obj.get('event_id'), obj.get('event_level'))
    
    @classmethod
    def load_from_yaml(cls, file_path):
        print("load comments from", file_path)
        if not os.path.exists(file_path):
            print(f"{file_path} not found")
            return []

        with open(file_path, 'r') as f:
            data = yaml.safe_load(f) or []

        return [Comment.from_dict(obj) for obj in data]

    @classmethod
    def save_to_yaml(cls, file_path, comments):
        with open(file_path, 'w') as f:
            yaml.dump([c.__dict__ for c in comments], f)