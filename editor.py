import logging
import subprocess
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip, concatenate_videoclips, TextClip
from moviepy.video.fx import MultiplySpeed, Resize, CrossFadeIn, CrossFadeOut
import numpy as np
import os
from voicer import Voicer
from utils import format_time
from event import Tag
import cv2

PREVIEW_BUFFER = 2
DELAY_BEFORE_REPLAY = 6
REPLAY_BUFFER = 2
HIGHLIGHT_EXTEND = 3
INTERRUPT_BUFFER = 0.5
LOGO_STAY = 0.5
LOGO_FLY = 0.8
TEMP_VIDEO_NAME = 'temp.mp4'
TEMP_AUDIO_NAME = 'temp.aac'

# 剪辑器
class Editor:
    # 初始化剪辑器
    def __init__(self, game):
        self.game = game
        self.voicer = Voicer(game)
        self.logo_clips = []
        self.replay_clips = []
        self.scoreboard_clips = []
        self.comment_audio = None
        self.current_score = None
        self.logo_times = None
        self.load_logo_video()
    
    def load_logo_video(self):
        logo_video_cap = cv2.VideoCapture(self.game.logo_video)
        fps = logo_video_cap.get(cv2.CAP_PROP_FPS)
        frames = []
        while True:
            ret, frame = logo_video_cap.read()
            if not ret:
                break
            frames.append(frame)

        duration = len(frames) / fps
        logo_video_cap.release()
        self.logo_video = {"fps": fps, "duration": duration, "frames": frames}
        print(f"loading logo video {self.game.logo_video} with {self.logo_video['fps']} fps and {self.logo_video['duration']} duration")

    # 预览比赛视频中配音解说的部分
    def preview(self):
        self.add_comment_voices()
        logging.info(f"comment audio duration: {self.comment_audio.duration}")

        clips = []
        for index, event in enumerate(self.game.events):
            if event.type.level < 8:
                continue
            clip = self.main_video.subclipped(event.time - PREVIEW_BUFFER, event.time + PREVIEW_BUFFER)
            clip.audio = self.comment_audio.subclipped(event.time - PREVIEW_BUFFER, event.time + PREVIEW_BUFFER)
            text_clip = TextClip(text=f"event-{index}: {event.type} {format_time(event.time)}", font_size=24, color='white', font='ROGFonts-Regular_0.otf').with_duration(clip.duration)
            clips.append(CompositeVideoClip([clip, text_clip.with_position(("center", "top"))]))

        # 连接有解说的片段并保存为预览视频
        concatenate_videoclips(clips).write_videofile('preview.mp4', threads=32, fps=16, preset='ultrafast')

    def edit(self):
        if not os.path.exists(TEMP_VIDEO_NAME):
            self.create_output_video()
        if not os.path.exists(TEMP_AUDIO_NAME):
            self.create_output_audio()
        self.add_audio()

    def create_output_video(self):
        cap = cv2.VideoCapture(self.game.main_video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(TEMP_VIDEO_NAME, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

        replay_events = self.calculate_replay_times()
        print(f"found {len(replay_events)} replay events")
        self.calculate_logo_times(replay_events)
        replay_frames = []
        replay_time = None
        processing_replay_event = None
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            time = frame_count / fps
            if frame_count % 10 == 0:
                print(f"frame {frame_count} / {cap.get(cv2.CAP_PROP_FRAME_COUNT)}", end="\r")

            if processing_replay_event is None:
                first_replay_event_time = len(replay_events) > 0 and replay_events[0].time or -100
                if time > first_replay_event_time - REPLAY_BUFFER and time < first_replay_event_time + REPLAY_BUFFER:
                    processing_replay_event = replay_events.pop(0)
                    print(f"processing replay event {processing_replay_event.type.name} {format_time(processing_replay_event.time)}")
                    replay_frame = frame.copy()
                    replay_frames.append(replay_frame)
                    replay_frames.append(replay_frame)
            else:
                if time > processing_replay_event.time - REPLAY_BUFFER and time < processing_replay_event.time + REPLAY_BUFFER:
                    replay_frame = frame.copy()
                    replay_frames.append(replay_frame)
                    replay_frames.append(replay_frame)
                else:
                    print(f"processed replay event {processing_replay_event.type.name} {format_time(processing_replay_event.time)}")
                    replay_time = processing_replay_event.replay_time
                    processing_replay_event = None

            if replay_time is not None and time > replay_time:
                if len(replay_frames) > 0:
                    frame = replay_frames.pop(0)
                else:
                    replay_time = None

            frame_count += 1

            self.draw_scoreboard(time, frame)
            self.draw_logo(time, frame)
            out.write(frame)

        out.release()  # release the cv2's VideoWriter
        cap.release()

    def create_output_audio(self):
        self.voicer.make_voice()
        audio_clips = [VideoFileClip(self.game.main_video).audio]
        last_comment = None
        for comment in self.game.comments:
            if not comment.text:
                continue
            voice_path = self.voicer.get_voice(comment.text)["path"]
            logging.info(f"voice path: {voice_path}")
            voice_clip = AudioFileClip(voice_path).with_volume_scaled(2)
            last_comment_end = last_comment.time + audio_clips[-1].duration if last_comment else 0
            if comment.time < last_comment_end:
                logging.info("overlapping comments, skipping lower level")
                if comment.event_level < last_comment.event_level:
                    logging.info(f"skipping comment {comment.text}")
                    continue
                if last_comment.time < comment.time - INTERRUPT_BUFFER:
                    logging.info(f"interrupt last comment {last_comment.text}")
                    audio_clips[-1] = audio_clips[-1].subclipped(0, comment.time - last_comment.time - INTERRUPT_BUFFER)
                else:
                    logging.info(f"skipping last comment {last_comment.text}")
                    audio_clips.pop()
                    last_comment = None

            logging.info(f"Adding voice for comment {comment.text} at {comment.time}")
            audio_clips.append(voice_clip.with_start(comment.time))
            last_comment = comment
        CompositeAudioClip(audio_clips).write_audiofile(TEMP_AUDIO_NAME, codec="aac")

    def add_audio(self):
        command = f"ffmpeg -i {TEMP_VIDEO_NAME} -i {TEMP_AUDIO_NAME} -c:v copy -c:a aac -strict experimental output.mp4 -y"
        subprocess.run(command, shell=True)
        os.remove(TEMP_VIDEO_NAME)
        os.remove(TEMP_AUDIO_NAME)

    def draw_scoreboard(self, time, frame):
        if time < self.game.start or time > self.game.end:
            return

        if len(self.game.score_updates) > 0 and time > self.game.score_updates[0].time:
            self.current_score = self.game.score_updates.pop(0)

        if self.current_score is not None:
            self.game.scoreboard.render_frame(frame, time - self.game.start, self.current_score.score0, self.current_score.score1)

    def calculate_logo_times(self, replay_events):
        self.logo_times = []
        for replay_event in replay_events:
            self.logo_times.append(replay_event.replay_time - self.logo_video["duration"] / 2)
            self.logo_times.append(replay_event.replay_time + REPLAY_BUFFER * 4 - self.logo_video["duration"] / 2)

    def draw_logo(self, time, frame):
        first_logo_time = len(self.logo_times) > 0 and self.logo_times[0] or None

        if first_logo_time is None:
            return

        if time > first_logo_time + self.logo_video["duration"]:
            print(f"logo time {first_logo_time} + {self.logo_video['duration']} is past, popping logo time")
            if len(self.logo_times) > 0:
                self.logo_times.pop(0)
            return;

        if time >= first_logo_time:
            logo_time = time - first_logo_time
            logo_frame_index = int(logo_time * self.logo_video["fps"])
            logo_frame = self.logo_video["frames"][logo_frame_index]
            if logo_time < LOGO_FLY / 2:
                alpha = 1 - logo_time / (LOGO_FLY / 2)
            elif logo_time > self.logo_video["duration"] - LOGO_FLY / 2:
                alpha = 1 - (self.logo_video["duration"] - logo_time) / (LOGO_FLY / 2)
            else:
                alpha = 0

            cv2.addWeighted(frame, alpha, logo_frame, 1 - alpha, 0, frame)
            cv2.putText(frame, f"logo time: {logo_time:.2f} frame: {logo_frame_index}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    # 创建重放片段
    def create_replays(self):
        # pick replay events
        replay_events = self.calculate_replay_times()
        logging.info(f"found {len(replay_events)} replay events")
        logo_video_duration = self.logo_video.duration

        last_main_time = 0
        for event in replay_events:
            logging.info(f"Replay event {event.type.name}: {format_time(event.time)}")
            logo_clip_before = self.logo_video.with_start(event.replay_time - logo_video_duration / 2).with_position(("center", "center")).with_effects([CrossFadeIn(LOGO_FLY / 2).copy(), CrossFadeOut(LOGO_FLY / 2).copy()])
            replay_clip = self.main_video.subclipped(event.time - REPLAY_BUFFER, event.time + REPLAY_BUFFER).without_audio().with_effects([MultiplySpeed(0.5)]).with_start(event.replay_time)
            logo_clip_after = self.logo_video.with_start(replay_clip.end - logo_video_duration / 2).with_position(("center", "center")).with_effects([CrossFadeIn(LOGO_FLY / 2).copy(), CrossFadeOut(LOGO_FLY / 2).copy()])

            self.replay_clips.append(replay_clip)
            self.logo_clips.append(logo_clip_before)
            self.logo_clips.append(logo_clip_after)

    # 计算重放片段的时间
    def calculate_replay_times(self):
        # 获取所有需要重放的事件
        replay_events = [e for e in self.game.events if Tag.Replay in e.tags]
        if not replay_events:
            return

        # 获取所有deadball时间段
        deadballs = self.game.deadballs
        if not deadballs:
            return

        # 按时间正序排序deadball和重放事件
        deadballs.sort(key=lambda x: x.start)
        replay_events.sort(key=lambda x: x.time)

        replay_duration = REPLAY_BUFFER * 2 * 2

        for deadball in deadballs:
            logging.info(f"calculate replay in deadball [{format_time(deadball.start)}-{format_time(deadball.end)}]")
            # 如果deadball时间太短，跳过
            if deadball.duration < replay_duration:
                logging.info("duration is too short, skipping")
                continue
            
            # 找到deadball之前最近的事件
            nearest_event = None
            for event in replay_events:
                if event.time <= deadball.start:
                    if event.replay_time is None:
                        nearest_event = event
                else:
                    break
            
            if nearest_event:
                # 计算居中播放的时间
                center_time = deadball.start + (deadball.duration - replay_duration) / 2
                nearest_event.replay_time = center_time
                logging.info(f"replay event: {nearest_event.type.name} {format_time(nearest_event.time)} at {format_time(center_time)}")
        
        return [e for e in replay_events if e.replay_time]

    # 创建精彩瞬间片段
    def create_hightlights_clip(self, game_clip, type=None, comment=None):
        clips = []
        logo_clips = []
        last_highlight_end = 0

        for event in self.game.events:
            if Tag.Replay in event.tags:
                logo_clips.append(self.create_logo_clip(last_highlight_end))
                highlight_clip = game_clip.subclipped(event.time - REPLAY_BUFFER, event.time + REPLAY_BUFFER + HIGHLIGHT_EXTEND).with_start(last_highlight_end)
                clips.append(highlight_clip)
                replay_clip = game_clip.subclipped(event.time - REPLAY_BUFFER, event.time + REPLAY_BUFFER).with_effects([MultiplySpeed(0.5)]).without_audio().with_start(highlight_clip.end)
                clips.append(replay_clip)
                last_highlight_end = replay_clip.end

        highlights_clip = CompositeVideoClip(clips + logo_clips)
        audio_clips = [highlights_clip.audio]

        if comment:
            voice = self.voicer.make_text_voice(comment)
            voice_clip = AudioFileClip(voice).with_volume_scaled(2)
            audio_clips.append(voice_clip)
            audio_clips[0] = audio_clips[0].subclipped(voice_clip.duration, audio_clips[0].duration).with_start(voice_clip.duration)

        if self.bgm:
            bgm_clips = []
            last_bgm_end = 0

            while last_bgm_end < highlights_clip.duration:
                if highlights_clip.end - last_bgm_end > self.bgm.duration:
                    current_bgm_clip = self.bgm.copy()
                else:
                    current_bgm_clip = self.bgm.subclipped(0, highlights_clip.duration - last_bgm_end)

                bgm_clips.append(current_bgm_clip.with_start(last_bgm_end))
                last_bgm_end = bgm_clips[-1].end
                
            audio_clips.extend(bgm_clips)

        if len(audio_clips) > 1:
            highlights_clip.audio = CompositeAudioClip(audio_clips)

        return highlights_clip
