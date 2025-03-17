from utils import parse_time
import os


class VideoDescription:
    def __init__(self, start, end, description):
        self.start = parse_time(start)
        self.end = parse_time(end)
        self.description = description

    @classmethod
    def from_line(cls, line):
        start, end, description = line.strip().split(': ')
        return cls(start, end, description)

    @classmethod
    def load_from_file(cls, file_path):
        if not os.path.exists(file_path):
            return []

        with open(file_path, 'r') as f:
            return [cls.from_line(line) for line in f.readlines()]

    def __str__(self):
        return f"{self.start} - {self.end}: {self.description}"


