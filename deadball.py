from utils import format_time, parse_time

class Deadball:
    def __init__(self, start, end=None):
        self.start = parse_time(start)
        self.end = parse_time(end)

    @property
    def is_closed(self):
        return self.end is not None

    def close(self, time):
        self.end = time

    @property
    def duration(self):
        return self.end - self.start

    def __repr__(self):
        return f"Deadball(start={format_time(self.start)}, end={format_time(self.end)})"

