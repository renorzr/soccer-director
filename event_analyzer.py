import random
import pickle
import os
from comment import Comment
from ai import ChatAI
from event import EventType, Tag
from deadball import Deadball

IDLE_COMMENT_TIME = 30
BATCH_SIZE = 10

# 事件分析器
class EventAnalyzer:
    # 初始化事件分析器
    def __init__(self, game):
        self.game = game
        self.current_deadball = None

    # 分析事件(生成解说词, 更新比分, 更新死球状态)
    def analyze(self):
        if os.path.exists(f'game.{self.game.game_id}.pkl'):
            with open(f'game.{self.game.game_id}.pkl', 'rb') as f:
                game_data = pickle.load(f)
                comments = self.game.comments = game_data['comments']
                self.game.score_updates = game_data['score_updates']
                self.game.deadballs = game_data['deadballs']
            return

        comments = self.game.comments = []
        self.game.deadballs = []
        
        game_info = f"比赛名称：{self.game.name}\n"
        game_info += f"{self.game.teams[0].color}队服: {self.game.teams[0].name}队\n"
        game_info += f"{self.game.teams[1].color}队服: {self.game.teams[1].name}队\n"
        game_info += f"目前是第{self.game.quarter}节，比分是{self.game.teams[0].score}:{self.game.teams[1].score}\n" if self.game.quarter else ""
        game_info += f"其它信息：{self.game.description}\n" if self.game.description else ""
        game_info += f"其它要求：{self.game.comment_requirement}\n" if self.game.comment_requirement else ""

        chat_ai = ChatAI()

        prompt = f"你是足球解说员\"{self.game.narrator}\"，我会发送给你比赛事件描述和解说要求，每次请生成一行解说词，提及球员名字时请用使用引号，可以省略球队和号码，如果不知道球员名字可以说xx队的x号。\n"
        prompt += "每次事件将以事件代码开头，然后是事件主体球队、队员和描述(N/A 表示未知或不可用)。事件代码的含义以及解说要求如下：\n"
        prompt += "Idle: 没有特别的事 要求：根据比赛信息和场上态势简短点评"
        prompt += "EndQuater: 一节比赛结束 要求：宣布第x节比赛结束，简短点评，提醒观众下一节马上开始。"
        prompt += "Intro: 开场前的介绍 要求：开场解说词，如果不是第一节，请补充上一节比分是x:x"
        for event_type in EventType:
            prompt += f"{event_type.name}: {event_type.event_name} {'要求：' + event_type.req if event_type.req else ''}\n"
        prompt += "以下比赛信息供参考：\n" + game_info
        prompt += "明白请回复\"ok\""
        
        chat_ai.chat(prompt)

        last_comment_time = self.game.start
        for event in self.game.events:
            self.update_deadball(event)
            
            for time in range(int(last_comment_time + IDLE_COMMENT_TIME), int(event.time) - 10, int(IDLE_COMMENT_TIME)):
                comments.append(Comment(time, chat_ai.chat("Idle"), 'Idle'))

            if event.type == EventType.Start:
                intro_time = event.time - 30 if event.time - 30 > 0 else 0
                comments.append(Comment(intro_time, chat_ai.chat("Intro"), 'event', event.id, event.type.level))
            elif event.type == EventType.End:
                if self.game.quarter < 4:
                    comments.append(Comment(event.time, chat_ai.chat("EndQuater"),'event', event.id, event.type.level))
                    continue
            elif event.type == EventType.Goal:
                comments.append(Comment(event.time, shoot_text(), 'event', event.id, event.type.level))
                event.time += 1
                self.game.update_score(event.time, event.team, self.game.teams[event.team].score + 1)
                event.desc = (event.desc or '') + f", 比分被改写为{self.game.teams[0].score}:{self.game.teams[1].score}"
            elif event.type == EventType.Miss:
                comments.append(Comment(event.time, shoot_text(), 'event', event.id, event.type.level))
                event.time += 1
            elif event.type == EventType.Comment:
                comments.append(Comment(event.time, event.desc, 'event', event.id, event.type.level))
                continue

            comments.append(self.event_comment(chat_ai, event))

            last_comment_time = event.time

        with open(f'game.{self.game.game_id}.pkl', 'wb') as f:
            pickle.dump({'comments': comments, 'score_updates': self.game.score_updates, 'deadballs': self.game.deadballs}, f)

    # 生成事件解说词
    def event_comment(self, chat_ai, event):
        text = chat_ai.chat(self.event_prompt(event))
        return Comment(event.time, text, 'event', event.id, event.type.level)

    # 生成事件解说词提示
    def event_prompt(self, event):
        return f"{event.type.name}: 球队: {self.game.teams[event.team].name if event.team is not None else 'N/A' } 队员：{event.player or 'N/A'} 描述: {event.desc or 'N/A'}"

    # 更新死球状态
    def update_deadball(self, event):
        if Tag.Deadball in event.tags and self.current_deadball is None:
            self.current_deadball = Deadball(event.time)
        elif Tag.Liveball in event.tags and self.current_deadball is not None:
            self.current_deadball.close(event.time)
            self.game.deadballs.append(self.current_deadball)
            self.current_deadball = None


# 射门解说词
def shoot_text():
    return random.choice(['打门！', '射门！'])