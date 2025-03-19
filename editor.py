from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip, concatenate_videoclips
from moviepy.video.fx import MultiplySpeed, Resize, CrossFadeIn, CrossFadeOut
import numpy as np
import os

DELAY_BEFORE_REPLAY = 6
REPLAY_BUFFER = 2
HIGHLIGHT_EXTEND = 1
INTERRUPT_BUFFER = 0.5
LOGO_STAY = 0.5
LOGO_FLY = 0.8

class Editor:
    def __init__(self, match):
        self.match = match
        self.clips = []
        self.logo_clips = []
        self.replay_clips = []
        self.scoreboard_clips = []
        self.main_video = VideoFileClip(self.match.main_video)
        self.logo_img = ImageClip(self.match.logo_img).with_effects([Resize(self.main_video.size)])
        self.logo_video = self.load_logo_video()
        self.bgm = AudioFileClip(self.match.bgm) if self.match.bgm and os.path.exists(self.match.bgm) else None
        self.comment_audio = None


    def edit(self, voicer=None):
        self.create_replays()
        self.create_scoreboards()
        if voicer is not None:
            self.add_comment_voices(voicer)


    def create_replays(self):
        # pick most important events
        events = [e for e in self.match.events if e.level >= 8]

        logo_video_duration = self.logo_video.duration

        last_main_time = 0
        for i in range(len(events)):
            event = events[i]
            next_event = events[i + 1] if i < len(events) - 1 else None
            if next_event and next_event.start < event.end + DELAY_BEFORE_REPLAY + 2 * (next_event.start - event.end + REPLAY_BUFFER * 2) + logo_video_duration:
                continue
            main_clip_before = self.main_video.subclipped(last_main_time, event.end + DELAY_BEFORE_REPLAY + logo_video_duration / 2).with_start(last_main_time)
            logo_clip_before = self.logo_video.with_start(main_clip_before.end - logo_video_duration / 2).with_position(("center", "center")).with_effects([CrossFadeIn(LOGO_FLY / 2).copy(), CrossFadeOut(LOGO_FLY / 2).copy()])
            replay_clip = self.main_video.subclipped(event.start - REPLAY_BUFFER, event.end + REPLAY_BUFFER).without_audio().with_effects([MultiplySpeed(0.5)]).with_start(main_clip_before.end)
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


    def create_scoreboards(self):
        if not self.match.score_updates:
            # 如果没有任何比分更新，创建一个0:0的记分牌从开始到结束
            self.render_scoreboard(self.match.start, self.match.end, 0, 0)
            return

        # 从后往前处理每个更新
        updates = self.match.score_updates
        for i in range(len(updates) - 1, -1, -1):
            current_update = updates[i]
            next_time = self.match.end if i == len(updates) - 1 else updates[i + 1].time
            
            self.render_scoreboard(
                current_update.time,
                next_time,
                current_update.score0,
                current_update.score1
            )
        
        # 处理比赛开始到第一次更新之间的时间段
        if updates[0].time > self.match.start:
            self.render_scoreboard(self.match.start, updates[0].time, 0, 0)


    def render_scoreboard(self, start_time, end_time, score0, score1):
        print(f"render scoreboard {start_time} to {end_time} with {score0}:{score1}")
        self.scoreboard_clips.append(
            self.match.scoreboard.render(self.match.game_time(start_time), end_time - start_time, score0, score1)
                .with_start(start_time)
                .with_position(("center", "bottom"))
        )
        

    def add_comment_voices(self, voicer):
        audio_clips = []
        last_comment = None
        for comment in self.match.comments:
            voice_path = voicer.get_voice(comment)
            print(f"voice path: {voice_path}")
            voice_clip = AudioFileClip(voice_path).with_volume_scaled(2)
            last_comment_end = last_comment.time + audio_clips[-1].duration if last_comment else 0
            if comment.time < last_comment_end:
                print("overlapping comments, skipping lower level")
                if comment.event_level < last_comment.event_level:
                    print("skipping comment", comment.text)
                    continue
                if last_comment.time < comment.time - INTERRUPT_BUFFER:
                    print("interrupt last comment", last_comment.text)
                    audio_clips[-1] = audio_clips[-1].subclipped(0, comment.time - last_comment.time - INTERRUPT_BUFFER)
                else:
                    print("skipping last comment", last_comment.text)
                    audio_clips.pop()
                    last_comment = None
            print(f"Adding voice for comment {comment.text} at {comment.time}")
            audio_clips.append(voice_clip.with_start(comment.time))
            last_comment = comment
        self.comment_audio = CompositeAudioClip(audio_clips)

    def save(self, start=0, end=None):
        final_clip = self.composite(start, end)
        final_clip.write_videofile(f'output.{self.match.match_id}.mp4', threads=32, fps=24, preset='ultrafast')

    def preview(self, start=0, end=None):
        final_clip = self.composite(start, end)
        final_clip.preview()

    def composite(self, start=0, end=None):

        final_clip = CompositeVideoClip(self.clips + self.replay_clips + self.scoreboard_clips + self.logo_clips)
        if self.comment_audio:
            final_clip.audio=CompositeAudioClip([final_clip.audio, self.comment_audio])

        final_clip.write_videofile(f'final.{self.match.match_id}.mp4', threads=32, fps=24, preset='ultrafast')
        final_clip = VideoFileClip(f'final.{self.match.match_id}.mp4')

        hightlights_clip = self.create_hightlights_clip(final_clip)
        hightlights_clip.write_videofile(f'highlights.{self.match.match_id}.mp4', threads=32, fps=24, preset='ultrafast')
        hightlights_clip = VideoFileClip(f'highlights.{self.match.match_id}.mp4')

        logo_clip = self.create_logo_clip(final_clip.duration)
        final_clip = concatenate_videoclips([final_clip, hightlights_clip, logo_clip])

        if not end:
            return final_clip

        print(f"Subclipping from {start} to {end}")
        return final_clip.subclipped(start, end)

    def create_hightlights_clip(self, final_clip):
        clips = []
        logo_clips = []
        last_highlight_end = 0

        for event in self.match.events:
            if event.level >= 8:
                highlight_clip = final_clip.subclipped(event.start - REPLAY_BUFFER, event.end + REPLAY_BUFFER + HIGHLIGHT_EXTEND).with_start(last_highlight_end)
                clips.append(highlight_clip)
                logo_clips.append(self.create_logo_clip(highlight_clip.end))
                replay_clip = final_clip.subclipped(event.start - REPLAY_BUFFER, event.end + REPLAY_BUFFER).with_effects([MultiplySpeed(0.5)]).without_audio().with_start(highlight_clip.end)
                clips.append(replay_clip)
                last_highlight_end = replay_clip.end
                logo_clips.append(self.create_logo_clip(last_highlight_end))

        highlights_clip = CompositeVideoClip(clips + logo_clips)

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
                
            highlights_clip.audio = CompositeAudioClip([highlights_clip.audio, *bgm_clips])

        return highlights_clip

    def get_frame(self, time):
        return self.main_video.get_frame(time)

    def get_duration(self):
        return self.main_video.duration

    def create_logo_clip(self, time):
        return self.logo_video.with_start(time - self.logo_video.duration / 2).with_position(("center", "center")).with_effects([CrossFadeIn(LOGO_FLY / 2).copy(), CrossFadeOut(LOGO_FLY / 2).copy()])

    def create_logo_video(self, stay=LOGO_STAY):
        clip = self.logo_img
        puff_in_clip = clip.with_effects([Resize(lambda t: (2 * (LOGO_FLY - t) / LOGO_FLY) + 1)]).with_position(("center", "center")).with_duration(LOGO_FLY)
        stay_clip = clip.with_duration(stay).with_start(puff_in_clip.end).with_position(("center", "center"))
        puff_out_clip = clip.with_effects([Resize(lambda t: 2 * t / LOGO_FLY + 1)]).with_start(stay_clip.end).with_position(("center", "center")).with_duration(LOGO_FLY)

        CompositeVideoClip([puff_in_clip, stay_clip, puff_out_clip]).write_videofile('logo.mp4', threads=32, fps=24, preset='ultrafast')
        return VideoFileClip('logo.mp4')

    def load_logo_video(self):
        if not self.match.logo_video or not os.path.exists(self.match.logo_video):
            return self.create_logo_video()
        else:
            return VideoFileClip(self.match.logo_video).with_effects([Resize(self.main_video.size)])


def is_video(path):
    return path.endswith('.mp4') or path.endswith('.avi') or path.endswith('.mov')