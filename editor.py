import logging
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip, concatenate_videoclips, TextClip
from moviepy.video.fx import MultiplySpeed, Resize, CrossFadeIn, CrossFadeOut
import numpy as np
import os
from voicer import Voicer
from utils import format_time
from event import Tag

PREVIEW_BUFFER = 2
DELAY_BEFORE_REPLAY = 6
REPLAY_BUFFER = 2
HIGHLIGHT_EXTEND = 3
INTERRUPT_BUFFER = 0.5
LOGO_STAY = 0.5
LOGO_FLY = 0.8

# 剪辑器
class Editor:
    # 初始化剪辑器
    def __init__(self, game):
        self.game = game
        self.voicer = Voicer(game)
        self.clips = []
        self.logo_clips = []
        self.replay_clips = []
        self.scoreboard_clips = []
        self.main_video = VideoFileClip(self.game.main_video)
        self.logo_img = ImageClip(self.game.logo_img).with_effects([Resize(self.main_video.size)])
        self.logo_video = self.load_logo_video()
        self.bgm = AudioFileClip(self.game.bgm) if self.game.bgm and os.path.exists(self.game.bgm) else None
        self.comment_audio = None

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


    # 剪辑比赛视频
    def edit(self):
        if os.path.exists(f'game.{self.game.game_id}.mp4'):
            logging.info(f"game {self.game.game_id} already exists, skipping")
            return

        self.create_replays()
        self.create_scoreboards()
        self.add_comment_voices()


    # 创建重放片段
    def create_replays(self):
        # pick replay events
        replay_events = self.calculate_replay_times()
        logging.info(f"found {len(replay_events)} replay events")
        logo_video_duration = self.logo_video.duration

        last_main_time = 0
        for event in replay_events:
            logging.info(f"Replay event {event.type.name}: {format_time(event.time)}")
            main_clip_before = self.main_video.subclipped(last_main_time, event.replay_time + logo_video_duration / 2).with_start(last_main_time)
            logo_clip_before = self.logo_video.with_start(main_clip_before.end - logo_video_duration / 2).with_position(("center", "center")).with_effects([CrossFadeIn(LOGO_FLY / 2).copy(), CrossFadeOut(LOGO_FLY / 2).copy()])
            replay_clip = self.main_video.subclipped(event.time - REPLAY_BUFFER, event.time + REPLAY_BUFFER).without_audio().with_effects([MultiplySpeed(0.5)]).with_start(main_clip_before.end)
            logo_clip_after = self.logo_video.with_start(replay_clip.end - logo_video_duration / 2).with_position(("center", "center")).with_effects([CrossFadeIn(LOGO_FLY / 2).copy(), CrossFadeOut(LOGO_FLY / 2).copy()])
            last_main_time = last_main_time + main_clip_before.duration + replay_clip.duration
            replay_clip.audio = self.main_video.audio.subclipped(replay_clip.start, replay_clip.end).with_start(replay_clip.start)

            self.clips.append(main_clip_before)
            self.replay_clips.append(replay_clip)
            self.logo_clips.append(logo_clip_before)
            self.logo_clips.append(logo_clip_after)

        if last_main_time < self.main_video.duration:
            main_clip_after = self.main_video.subclipped(last_main_time, self.main_video.duration).with_start(last_main_time)
            self.clips.append(main_clip_after)

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

    # 创建记分牌片段
    def create_scoreboards(self):
        if not self.game.score_updates:
            # 如果没有任何比分更新，创建一个0:0的记分牌从开始到结束
            self.render_scoreboard(self.game.start, self.game.end, 0, 0)
            return

        # 从后往前处理每个更新
        updates = self.game.score_updates
        next_time = self.game.end
        for i in range(len(updates) - 1, -1, -1):
            current_update = updates[i]
            
            self.render_scoreboard(
                current_update.time,
                next_time,
                current_update.score0,
                current_update.score1
            )

            next_time = current_update.time
        
        # 处理比赛开始到第一次更新之间的时间段
        if updates[0].time > self.game.start:
            self.render_scoreboard(self.game.start, updates[0].time, 0, 0)

    # 渲染记分牌片段
    def render_scoreboard(self, start_time, end_time, score0, score1):
        logging.info(f"render scoreboard {start_time} to {end_time} with {score0}:{score1}")
        self.scoreboard_clips.append(
            self.game.scoreboard.render(self.game.game_time(start_time), end_time - start_time, score0, score1)
                .with_start(start_time)
                .with_position(("center", "bottom"))
        )
        
    # 添加配音解说
    def add_comment_voices(self):
        self.voicer.make_voice()
        audio_clips = []
        last_comment = None
        for comment in self.game.comments:
            if not comment.text:
                continue
            voice_path = self.voicer.get_voice(comment.text)
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
        self.comment_audio = CompositeAudioClip(audio_clips)

    # 保存比赛视频
    def save(self, start=0, end=None):
        final_clip = self.composite(start, end)
        final_clip.write_videofile(f'output.{self.game.game_id}.mp4', threads=32, fps=24, preset='ultrafast')

    # 合成比赛视频
    def composite(self, start=0, end=None):
        game_file = f'game.{self.game.game_id}.mp4'
        if not os.path.exists(game_file):
            game_clip = CompositeVideoClip(self.clips + self.replay_clips + self.scoreboard_clips + self.logo_clips)
            if self.comment_audio:
                game_clip.audio=CompositeAudioClip([game_clip.audio, self.comment_audio])
                game_clip.write_videofile(game_file, threads=32, fps=24, preset='ultrafast')
        game_clip = VideoFileClip(game_file)

        if end:
            logging.info(f"Subclipping from {format_time(start)} to {format_time(end)}")
            return game_clip.subclipped(start, end)

        highlights_file = f'highlights.{self.game.game_id}.mp4'
        if not os.path.exists(highlights_file):
            hightlights_clip = self.create_hightlights_clip(game_clip, comment="下面请观看本场比赛的精彩瞬间")
            hightlights_clip.write_videofile(highlights_file, threads=32, fps=24, preset='ultrafast')
        hightlights_clip = VideoFileClip(highlights_file)

        logo_clip = self.create_logo_clip(0)

        return concatenate_videoclips([logo_clip, game_clip, hightlights_clip])

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

    # 获取视频帧
    def get_frame(self, time):
        return self.main_video.get_frame(time)

    # 获取视频时长
    def get_duration(self):
        return self.main_video.duration

    # 创建logo片段
    def create_logo_clip(self, time):
        return self.logo_video.with_start(time - self.logo_video.duration / 2).with_position(("center", "center")).with_effects([CrossFadeIn(LOGO_FLY / 2).copy(), CrossFadeOut(LOGO_FLY / 2).copy()])

    # 创建logo视频
    def create_logo_video(self, stay=LOGO_STAY):
        clip = self.logo_img
        puff_in_clip = clip.with_effects([Resize(lambda t: (2 * (LOGO_FLY - t) / LOGO_FLY) + 1)]).with_position(("center", "center")).with_duration(LOGO_FLY)
        stay_clip = clip.with_duration(stay).with_start(puff_in_clip.end).with_position(("center", "center"))
        puff_out_clip = clip.with_effects([Resize(lambda t: 2 * t / LOGO_FLY + 1)]).with_start(stay_clip.end).with_position(("center", "center")).with_duration(LOGO_FLY)

        CompositeVideoClip([puff_in_clip, stay_clip, puff_out_clip]).write_videofile('logo.mp4', threads=32, fps=24, preset='ultrafast')
        return VideoFileClip('logo.mp4')

    # 加载logo片段
    def load_logo_video(self):
        if not self.game.logo_video or not os.path.exists(self.game.logo_video):
            return self.create_logo_video()
        else:
            return VideoFileClip(self.game.logo_video).with_effects([Resize(self.main_video.size)])


