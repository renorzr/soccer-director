import random
import pickle
import os
from comment import Comment
from utils import ChatAI

IDLE_COMMENT_TIME = 30
BATCH_SIZE = 10

class CommentWriter:
    def __init__(self, match):
        self.match = match


    def create_comments(self):
        comments = self.match.comments = Comment.load_from_yaml(f'comments.{self.match.match_id}.yaml')
        print(f"loaded {len(comments)} comments")

        if comments and os.path.exists(f'score_updates.{self.match.match_id}.pkl'):
            with open(f'score_updates.{self.match.match_id}.pkl', 'rb') as f:
                self.match.score_updates = pickle.load(f)
            return self.match.comments

        match_info = f"比赛名称：{self.match.name}\n"
        match_info += f"{self.match.teams[0].color}队服: {self.match.teams[0].name}队\n"
        match_info += f"{self.match.teams[1].color}队服: {self.match.teams[1].name}队\n"
        match_info += f"目前是第{self.match.quarter}节，比分是{self.match.teams[0].score}:{self.match.teams[1].score}\n" if self.match.quarter else ""
        match_info += f"其它信息：{self.match.description}\n" if self.match.description else ""

        chat_ai = ChatAI()
        if not self.match.quarter or self.match.quarter == 4:
            end_req = "先简短宣布比赛结束，突出即时性，然后补充比赛结果和点评，最后感谢观众收看。以下开头供参考：终场哨响；全场比赛结束；裁判员吹响了终场哨；比赛结束；等等。"
        else:
            end_req = "先简短宣布一节比赛结束，然后补充比赛结果和点评，并提醒下一节比赛稍后开始。以下开头供参考：第x节比赛结束；比赛告一段落；裁判吹响了第x节比赛结束的哨声；等等。"

        prompt = f"你是足球解说员\"{self.match.narrator}\"，我会发送给你比赛事件描述和解说要求，每次请生成一行解说词，提及球员名字时请用使用引号，如果不知道球员名字就说队员（如：6号\"张三\"或\"张三\"，11号队员等）。\n"
        prompt += "每次事件将以事件代码开头，然后是事件描述。事件代码的含义以及解说要求如下：\n"
        prompt += "idle: 比赛进行中 要求：点评当前比赛情况。以下话题供参考：目前是第x节，比分是x:x；x队攻势十分猛烈；x队防守十分严密；x队应该加强进攻；等等。\n"
        prompt += "intro: 开场前的介绍 要求：开场解说词，如果不是第一节，请补充上一节比分是x:x\n"
        prompt += "start: 比赛开始 要求：简短宣布比赛开始\n"
        prompt += "end: 比赛结束 要求：" + end_req
        prompt += "goal: 进球 要求：简短，以\"球进啦！\"、\"进了！\"、\"好球！\"等开头\n"
        prompt += "miss: 射门未进 要求：简短，以\"哎呀没进！\"、\"打偏了！\"、\"可惜！\"等开头\n"
        prompt += "foul: 犯规 要求：简短，以\"犯规！\"、\"裁判吹哨了！\"、\"犯规！\"等开头\n"
        prompt += "freekick: 任意球\n"
        prompt += "penalty: 点球\n"
        prompt += "breakthrough: 突破\n"
        prompt += "save: 扑救\n"
        prompt += "kickoff: 开球\n"
        prompt += "tackle: 抢断\n"
        prompt += "pass: 传球\n"
        prompt += "以下比赛信息供参考：\n" + match_info
        prompt += "明白请回复\"ok\""
        
        chat_ai.chat(prompt)

        last_comment_time = self.match.start
        for event in self.match.events:
            for time in range(int(last_comment_time + IDLE_COMMENT_TIME), int(event.start) - 10, int(IDLE_COMMENT_TIME)):
                comments.append(Comment(time, chat_ai.chat("idle"), 'idle'))

            if event.type == 'start':
                intro_time = event.start - 30 if event.start - 30 > 0 else 0
                comments.append(Comment(intro_time, chat_ai.chat("intro"), 'event', event.id, event.level))
                comments.append(self.event_comment(chat_ai, event))
            elif event.type == 'goal':
                self.match.update_score(event.end, event.team, self.match.teams[event.team].score + 1)
                comments.append(Comment(event.start, '射门！', 'event', event.id, event.level))
                event.desc = (event.desc or '') + f", 比分被改写为{self.match.teams[0].score}:{self.match.teams[1].score}"
                comments.append(self.event_comment(chat_ai, event))
            elif event.type == 'miss':
                comments.append(Comment(event.start, '射门！', 'event', event.id, event.level))
                comments.append(self.event_comment(chat_ai, event))
            elif event.type == 'freekick':
                comments.append(self.event_comment(chat_ai, event, on_start=True))
            elif event.type == 'description':
                comments.append(Comment(event.start, event.desc, 'event', event.id, event.level))
            else:
                comments.append(self.event_comment(chat_ai, event))

            last_comment_time = event.end

        with open(f'score_updates.{self.match.match_id}.pkl', 'wb') as f:
            pickle.dump(self.match.score_updates, f)

        Comment.save_to_yaml(f'comments.{self.match.match_id}.yaml', comments)

    def event_comment(self, chat_ai, event, on_start=False):
        text = chat_ai.chat(self.event_prompt(event))
        return Comment(event.start if on_start else event.end, text, 'event', event.id, event.level)

    def event_prompt(self, event):
        subject = self.match.teams[event.team].name if event.team is not None else ""
        subject += f"队的{event.player or '队员'}" if subject else ""
        return f"{event.type}: {subject} {event.desc or ''}"

