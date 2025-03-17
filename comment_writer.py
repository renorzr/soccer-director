import random
from comment import Comment
from utils import ChatAI

IDLE_COMMENT_TIME = 30
BATCH_SIZE = 10
EVENT_NAMES = {
    'start': '比赛开始',
    'end': '比赛结束',
    'goal': '进球',
    'miss': '射门未进',
    'foul': '犯规',
    'video_description': '视频描述',
    'pass': '传球',
    'tackle': '抢断',
    'corner': '角球',
    'freekick': '任意球',
    'penalty': '点球',
    'breakthrough': '突破',
    'clearance': '解围',
    'interception': '拦截',
    'save': '扑救',
    'offside': '越位',
}

class CommentWriter:
    def __init__(self, match):
        self.match = match


    def create_comments(self):
        comments = self.match.comments = Comment.load_from_yaml('comments.yaml')
        print(f"loaded {len(comments)} comments")

        if comments:
            return self.match.comments

        match_info = f"比赛名称：{self.match.name}\n"
        match_info += f"{self.match.teams[0].color}队服: {self.match.teams[0].name}队\n"
        match_info += f"{self.match.teams[1].color}队服: {self.match.teams[1].name}队\n"
        match_info += f"目前是第{self.match.quarter}节，上一节比赛比分是{self.match.teams[0].score}:{self.match.teams[1].score}\n" if self.match.quarter else ""
        match_info += f"其它信息：{self.match.description}\n" if self.match.description else ""

        chat_ai = ChatAI()
        chat_ai.chat(f"你是足球解说员\"{self.match.narrator}\"，我会发送给你比赛事件描述和解说要求，每次请生成一行解说词。以下比赛信息供参考：\n" + match_info)

        last_comment_time = self.match.start
        for event in self.match.events:
            for time in range(int(last_comment_time + IDLE_COMMENT_TIME), int(event.start) - 10, int(IDLE_COMMENT_TIME)):
                comments.append(Comment(time, chat_ai.chat(f"事件：比赛进行中\n要求：点评当前比赛情况。以下话题供参考：目前是第x节，比分是x:x；x队攻势十分猛烈；x队防守十分严密；x队应该加强进攻；等等。"), 'idle'))

            team = self.match.teams[event.team] if event.team else ""
            if event.type == 'start':
                intro_time = event.start - 30 if event.start - 30 > 0 else 0
                comments.append(Comment(intro_time, chat_ai.chat(f"事件：比赛即将开始\n要求：开场解说词"), 'event', event.id, event.level))
                comments.append(Comment(event.start, chat_ai.chat(f"事件：比赛开始"), 'event', event.id, event.level))
            elif event.type == 'end':
                if not self.match.quarter or self.match.quarter == 4:
                    comments.append(Comment(event.end, chat_ai.chat(f"事件：比赛结束\n要求：先简短宣布比赛结束，突出即时性，然后补充比赛结果和点评，最后感谢观众收看。以下开头供参考：终场哨响；全场比赛结束；裁判员吹响了终场哨；比赛结束；等等。"), 'event', event.id, event.level))
                else:
                    comments.append(Comment(event.end, chat_ai.chat(f"事件：第{self.match.quarter}节比赛结束\n要求：先简短宣布一节比赛结束，然后补充比赛结果和点评，并提醒下一节比赛稍后开始。以下开头供参考：第x节比赛结束；比赛告一段落；裁判吹响了第x节比赛结束的哨声；等等。"), 'event', event.id, event.level))
            elif event.type == 'goal':
                self.match.update_score(event.end, event.team, self.match.teams[event.team].score + 1)
                chat_ai.chat(f"事件：射门，射门的是{team}队的{event.player} \n要求：简短，突出即时性")
                comments.append(Comment(event.start, '射门！', 'event', event.id, event.level))
                event.desc = (event.desc or '') + f", 比分改写为{self.match.teams[0].score}:{self.match.teams[1].score}"
                comments.append(self.event_comment(chat_ai, event))
            elif event.type == 'miss':
                chat_ai.chat(f"事件：射门，射门的是{team}队的{event.player} \n要求：简短，突出即时性")
                comments.append(Comment(event.start, '射门！', 'event', event.id, event.level))
                comments.append(self.event_comment(chat_ai, event))
            elif event.type == 'foul':
                comments.append(self.event_comment(chat_ai, event, "简短，突出即时性。以下开头供参考：裁判吹哨，某某队员犯规了；裁判员吹哨了；等等。"))
            elif event.type == 'freekick':
                comments.append(self.event_comment(chat_ai, event, on_start=True))
            else:
                comments.append(self.event_comment(chat_ai, event))

            last_comment_time = event.end

        Comment.save_to_yaml('comments.yaml', comments)

    def event_comment(self, chat_ai, event, requirement=None, on_start=False):
        text = chat_ai.chat(self.event_prompt(event, requirement))
        return Comment(event.start if on_start else event.end, text, 'event', event.id, event.level)

    def event_prompt(self, event, requirement=None):
        subject = self.match.teams[event.team].name if event.team is not None else ""
        subject += f"队的{event.player or '队员'}"
        desc = '\n描述：' + event.desc if event.desc else ''
        req = '\n要求：' + requirement if requirement else ''
        return f"事件：{EVENT_NAMES[event.type]} {subject}{desc}{req}"

