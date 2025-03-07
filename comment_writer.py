from comment import Comment
from utils import request_ai

BATCH_SIZE = 10

class CommentWriter:
    def __init__(self, match):
        self.match = match
        self.events = self._select(match.events)

    def create_comments(self):
        # load comments if they exist
        self.match.comments = Comment.load_from_yaml('comments.yaml') or []

        # uncommented events
        last_comment_time = self.match.comments[-1].time if self.match.comments else 0
        print('last_comment_time', last_comment_time, 'events', self.events)
        events = [e for e in self.events if e.start > last_comment_time]
        print('events', events)
        for event in events:
            self._create_comments(event)

    def _create_comments(self, event):
        comments = self._create_event_comments(event)
        for i, comment in enumerate(comments):
            self.match.comments.append(comment)

        Comment.save_to_yaml('comments.yaml', self.match.comments)

    def _create_event_comments(self, event):
        if event.type == 'goal':
            return [Comment(event.start, "射门！", 'event', event.id, event.level), Comment(event.end, "球进了！", 'event', event.id, event.level)]
        elif event.type == 'foul':
            return [Comment(event.start, "犯规了", 'event', event.id, event.level)]
        elif event.type == 'start':
            prompt = f"""你是一名足球解说员，请根据以下信息生成比赛开始前的介绍：
            比赛名称：{self.match.name}
            {self.match.teams[0].color}队服: {self.match.teams[0].name}队
            {self.match.teams[1].color}队服: {self.match.teams[1].name}队
            """
            comments = [Comment(event.start - 10, request_ai(prompt), 'event', event.id, event.level)]
            comments.append(Comment(event.start, "比赛开始", 'event', event.id, event.level))
            return comments
        elif event.type == 'end':
            prompt = f"""你是一名足球解说员，请宣布比赛结束并根据以下信息生成简短总结：
            比赛名称：{self.match.name}
            {self.match.teams[0].color}队服: {self.match.teams[0].name}队
            {self.match.teams[1].color}队服: {self.match.teams[1].name}队
            比分：{self.match.teams[0].score}:{self.match.teams[1].score}
            """
            return [Comment(event.start, request_ai(prompt), 'event', event.id, event.level)]
        elif event.type == 'comment':
            return [Comment(event.start, event.desc, 'event', event.id, event.level)]
        elif event.type == 'pass':
            return [Comment(event.start, "传球！", 'event', event.id, event.level)]
        else:
            return []
            
    def _select(self, events):
        return [e for e in events if e.level > 5]