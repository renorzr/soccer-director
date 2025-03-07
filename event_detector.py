import yaml
from PIL import Image
import io
import base64
from event import Event
from utils import request_ai, format_time
from random import random


DETECT_BATCH_SIZE = 50
DETECT_FPS = 5
DETECT_IMAGE_WIDTH = 512

class EventDetector:
    def __init__(self, match, editor):
        self.match = match
        self.editor = editor
        self.manual_events = [Event.from_dict(e) for e in match.manual_events]
        
    def detect(self):
        # if saved events exist, load them
        self.match.events = Event.load_from_yaml('events.yaml')

        if not self.match.end:
            self.match.end = self.editor.get_duration()
            
        last_time = self.match.start or 0
        if self.match.events:
            last_time = self.match.events[-1].end
        else:
            self.match.events.append(Event('start', last_time, last_time))

        self.update_score(self.match.events)
        while last_time < self.match.end:
            new_events = self._detect_events(last_time)
            self.update_score(new_events)
            print("append events", new_events)
            self.match.events.extend(new_events)
            last_time += DETECT_BATCH_SIZE / DETECT_FPS
            # save events
            Event.save_to_yaml('events.yaml', self.match.events)

        if self.match.events[-1].type != 'end':
            self.match.events.append(Event('end', self.match.end, self.match.end))
            Event.save_to_yaml('events.yaml', self.match.events)

    def _detect_events(self, since):
        frames = []

        print(f"comment {DETECT_BATCH_SIZE} frames since {since}")
        for i in range(DETECT_BATCH_SIZE):
            time = since + i / DETECT_FPS
            frame = self.editor.get_frame(time)
            image = Image.fromarray(frame)
            detect_image_height = int(DETECT_IMAGE_WIDTH * image.height / image.width)
            image.thumbnail((DETECT_IMAGE_WIDTH, detect_image_height))
            frames.append(image)

        end_time = since + DETECT_BATCH_SIZE / DETECT_FPS
        [team0, team1] = self.match.teams
        manual_events = [e for e in self.manual_events if since <= e.start < end_time]
        last_event_desc = self.describe_event(manual_events[-1]) if manual_events else ''
        game_time = end_time - self.match.start

        prompt = f"你是足球比赛的解说员。这是一场足球比赛的视频片段，场上{team0.color}队服是{team0.name}队，{team1.color}队服是{team1.name}队。目前比赛进行到第{game_time}秒，比分({team0.score}:{team1.score})。{last_event_desc}请简短评论，无需描述所有信息，只输出一行。以下是之前的评论供参考，尽量不要重复：\n"
        events = [e for e in self.match.events if e.type == 'comment' and e.start < end_time][-5:]
        prompt += '\n'.join([f"{format_time(e.start - self.match.start)} {e.desc}" for e in events])

        response_text = request_ai(prompt)
        return [*manual_events, Event('comment', end_time, end_time, None, None, response_text)]


        # Parse the response
        #events = []
        #for line in response_text.split('\n'):
        #    parts = line.split(':')
        #    if len(parts) != 5:
        #        continue

        #    (event_type, start_frame, end_frame, team, description) = parts
        #    start_time = since + int(start_frame) / DETECT_FPS
        #    end_time = since + int(end_frame) / DETECT_FPS
        #    events.append(Event(event_type, start_time, end_time, team, description))

        #end_time = since + DETECT_BATCH_SIZE / DETECT_FPS
        #events.append(Event(0, 'empty', end_time, end_time))

    def describe_event(self, event):
        team = self.match.teams[event.team]
        player = event.player or '球员'
        if event.type == 'goal':
            return f"{team.name}队{player}进球！"
        else:
            return ""

    def update_score(self, events):
        for event in events:
            if event.type == 'goal':
                self.match.update_score(event.end, event.team, self.match.teams[event.team].score + 1)
            elif event.type in ['start', 'end']:
                self.match.update_score(event.start, None, None)


VIDEO_DETECT_PROMPT = """
These are frames from a soccer game video. Your task is to detect events in the video and output them in the following format:

**"event_type:start_frame:end_frame:team(optional):description(optional)"**

Where:
- **event_type** is one of the following:
    - **goal**: A goal scored.  
        - **start_frame**: When the player begins the shot.  
        - **end_frame**: When the ball enters the goal.
    - **miss**: A shot that misses the goal.  
        - **start_frame**: When the player begins the shot.  
        - **end_frame**: When the ball is stopped or goes out of bounds.
    - **save**: A goalkeeper saves the shot.  
        - **start_frame**: When the player begins the shot.  
        - **end_frame**: When the goalkeeper saves the ball.
    - **foul**: A player commits a foul.  
        - **start_frame**: When the foul starts.  
        - **end_frame**: When the referee blows the whistle.
    - **pass**: A player passes the ball.  
        - **start_frame**: When the player begins the pass.  
        - **end_frame**: When another player receives the ball.
    - **pass_fail**: A pass is intercepted.  
        - **start_frame**: When the player begins the pass.  
        - **end_frame**: When the ball is intercepted by another player.
    - **breakthru**: A player breaks through the defense.  
        - **start_frame**: When the player starts breaking through.  
        - **end_frame**: When the player successfully breaks through the defense.

### Notes:
- Make sure **start_frame** and **end_frame** represent the frame indices within the video, not time in seconds. 
- Only events on the field should be considered.
- For each event, leave the **description** and **team** empty if not relevant or detected.

### Example:
```
goal:20:30:blue:Blue team scores a goal.
```
"""

VIDEO_DETECT_PROMPT_CN = """这些是足球比赛视频的帧。检测视频中的事件。
#并按以下格式将每个事件输出到一行: event_type:start_frame:end_frame:team (如果检测到):description(可选)
#以下给出了event_type的取值以及不同取值下start_frame/end_frame的意义:
#  goal:射门得分, start_frame 是球员开始射门的帧, end_frame 是球入门的帧
#  miss:射门未进, start_frame 是球员开始射门的帧, end_frame 是球被拦截或确定射失的帧
#  save:守门员扑救, start_frame 是球员开始射门的帧, end_frame 是球被守门员扑救的帧
#  foul:球员犯规, start_frame 是球员开始犯规的帧, end_frame 是裁判吹哨的帧
#  pass:球员传球, start_frame 是球员开始传球的帧, end_frame 是其他球员接球的帧
#  pass_fail:球员传球被拦截, start_frame 是球员开始传球的帧, end frame 是其他球员拦截球的帧
#  breakthru:球员突破防守, start_frame 是球员开始突破的帧, end frame 是球员完成突破的帧
#注意:
#  1. start_frame/end_frame 取值是视频中帧的索引, 从0开始计数。
#  2. 仅考虑球场内事件。
#  3. 如果未检测到任何事件, 则留空。
#示例:
#  进球:20:30:blue:蓝队进球"""