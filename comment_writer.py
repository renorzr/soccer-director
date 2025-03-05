from comment import Comment

BATCH_SIZE = 10

class CommentWriter:
    def __init__(self, match):
        self.match = match
        self.events = self._select(match.events)

    def create_comments(self):
        # load comments if they exist
        self.match.comments = Comment.load_from_yaml('comments.yaml')

        # uncommented events
        last_comment_time = self.match.comments[-1].time if self.match.comments else 0
        events = [e for e in self.events if e.start > last_comment_time]
        for event in events:
            self._create_comments(event)

    def _create_comments(self, event):
        comments = self._create_event_comments(event)
        for i, comment in enumerate(comments):
            self.match.comments.append(comment)

        Comment.save_to_yaml('comments.yaml', self.match.comments)

    def _create_event_comments(self, event):
        if event.type == 'goal':
            return [Comment(event.start, "射门！", 'event', event.id), Comment(event.end, "球进了！", 'event', event.id)]
        elif event.type == 'foul':
            return [Comment(event.start, "犯规了", 'event', event.id)]
        elif event.type == 'start':
            return [Comment(event.start, "比赛开始", 'event', event.id)]
        elif event.type == 'end':
            return [Comment(event.start, "比赛结束", 'event', event.id)]
        elif event.type == 'comment':
            return [Comment(event.start, event.desc, 'event', event.id)]
            
    def _select(self, events):
        return [e for e in events if e.level > 5]