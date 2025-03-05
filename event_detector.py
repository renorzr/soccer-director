import yaml
from PIL import Image
import io
import base64
from event import Event
from utils import ai_client


DETECT_BATCH_SIZE = 50
DETECT_FPS = 5
DETECT_IMAGE_WIDTH = 512

class EventDetector:
    def __init__(self, match, editor):
        self.match = match
        self.editor = editor
        
    def detect(self):
        # if saved events exist, load them
        self.match.events = Event.load_from_yaml('events.yaml')

        if not self.match.end:
            self.match.end = self.editor.get_duration()
            
        last_time = self.match.start or 0
        if self.match.events:
            last_time = self.match.events[-1].end
        else:
            self.match.events.append(Event(0, 'start', last_time, last_time))

        while last_time < self.match.end:
            new_events = self._detect_events(last_time)
            print("append events", new_events)
            self.match.events.extend(new_events)
            last_time += DETECT_BATCH_SIZE / DETECT_FPS
            # save events
            Event.save_to_yaml('events.yaml', self.match.events)

        if self.match.events[-1].type != 'end':
            self.match.events.append(Event(0, 'end', self.match.end, self.match.end))
            Event.save_to_yaml('events.yaml', self.match.events)

    def _detect_events(self, since):
        base64frames = []
        frames = []

        print(f"Detecting events from {DETECT_BATCH_SIZE} frames since {since}")
        for i in range(DETECT_BATCH_SIZE):
            time = since + i / DETECT_FPS
            frame = self.editor.get_frame(time)
            image = Image.fromarray(frame)
            detect_image_height = int(DETECT_IMAGE_WIDTH * image.height / image.width)
            image.thumbnail((DETECT_IMAGE_WIDTH, detect_image_height))
            frames.append(image)
            #buffer = io.BytesIO()
            #image.save(buffer, format="JPEG")
            #image.save(f'frames/frame-{since:02}-{i:02}.jpg', format="JPEG")
            #base64frames.append(base64.b64encode(buffer.getvalue()).decode('utf-8'))

        #content = [
        #                {
        #                    "type": "text",
        #                    "text": VIDEO_DETECT_PROMPT
        #                },
        #                *map(lambda x: {"image_url": {"url": f"data:image/jpeg;base64,{x}"}, "type": "image_url"}, base64frames),
        #            ]

        ## Create OpenAI chat completion
        #print(f"Sending {len(base64frames)} frames to OpenAI")
        #response = ai_client.chat.completions.create(
        #    model="gpt-4o-mini",
        #    messages=[
        #        {
        #            "role": "user", 
        #            "content": content,
        #        }
        #    ],
        #    max_tokens=100,
        #)

        ## Print the response content
        #print('usage:', response.usage)
        #response_text = response.choices[0].message.content

        response = ai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[VIDEO_DETECT_PROMPT, *frames],)
        response_text = response.text
        print(response_text)


        # Parse the response
        events = []
        for line in response_text.split('\n'):
            parts = line.split(':')
            if len(parts) != 5:
                continue

            (event_type, start_frame, end_frame, team, description) = parts
            start_time = since + int(start_frame) / DETECT_FPS
            end_time = since + int(end_frame) / DETECT_FPS
            events.append(Event(level_of(event_type), event_type, start_time, end_time, team, description))

        end_time = since + DETECT_BATCH_SIZE / DETECT_FPS
        events.append(Event(0, 'empty', end_time, end_time))

        return events

def level_of(event_type):
    if event_type == 'goal':
        return 10

    if event_type == 'miss':
        return 9

    if event_type == 'foul':
        return 8
    
    if event_type == 'save':
        return 7
    
    return 5


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