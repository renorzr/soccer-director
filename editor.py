from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip, TextClip
from moviepy.video.fx import MultiplySpeed, Resize, CrossFadeIn, CrossFadeOut
import numpy as np

DELAY_BEFORE_REPLAY = 4
REPLAY_BUFFER = 2
INTERRUPT_BUFFER = 0.5
LOGO_STAY = 0.2
LOGO_FLY = 0.8
SCOREBOARD_DURATION = 20
SCOREBOARD_INTERVAL = 60

class Editor:
    def __init__(self, match):
        self.match = match
        self.clips = []
        self.logo_clips = []
        self.replay_clips = []
        self.scoreboard_clips = []
        self.main_video = VideoFileClip(self.match.main_video)
        self.logo_video = VideoFileClip(self.match.logo).with_effects([Resize(self.main_video.size)]) if is_video(self.match.logo) else self.create_logo_video(self.match.logo)
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
        for event in events:
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

        main_clip_after = self.main_video.subclipped(last_main_time, self.main_video.duration).with_start(last_main_time)
        self.clips.append(main_clip_after)


    def create_scoreboards(self):
        last_score_update = None
        print("score updates", self.match.score_updates)
        for update in self.match.score_updates:
            if last_score_update:
                for time in range(last_score_update.time + SCOREBOARD_INTERVAL, update.time, SCOREBOARD_INTERVAL):
                    self.render_scoreboard(time, last_score_update.score0, last_score_update.score1)

            self.render_scoreboard(update.time, update.score0, update.score1)


    def render_scoreboard(self, time, score0, score1):
        print(f"render scoreboard at {time} with {score0}:{score1}")
        self.scoreboard_clips.append(
            self.match.scoreboard.render(time - self.match.start, SCOREBOARD_DURATION, score0, score1)
                .with_start(time)
                .with_position(("center", "bottom"))
        )
        

    def add_comment_voices(self, voicer):
        audio_clips = []
        last_comment = None
        for comment in self.match.comments:
            voice_path = voicer.get_voice(comment)
            print(f"voice path: {voice_path}")
            voice_clip = AudioFileClip(voice_path)
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
        final_clip.write_videofile('output.mp4')

    def preview(self, start=0, end=None):
        final_clip = self.composite(start, end)
        final_clip.preview()

    def composite(self, start=0, end=None):
        final_clip = CompositeVideoClip(self.clips + self.scoreboard_clips + self.replay_clips + self.logo_clips)
        if self.comment_audio:
            final_clip.audio=CompositeAudioClip([final_clip.audio, self.comment_audio])

        if not end:
            return final_clip

        print(f"Subclipping from {start} to {end}")
        return final_clip.subclipped(start, end)


    def get_frame(self, time):
        return self.main_video.get_frame(time)

    def get_duration(self):
        return self.main_video.duration

    def create_logo_video(self, logo_path):
        clip = ImageClip(logo_path)
        screen_size = self.main_video.size
        white_blank_image = ImageClip(np.zeros((screen_size[1], screen_size[0], 3), dtype=np.uint8) + 255).with_duration(LOGO_FLY * 2 + LOGO_STAY).with_start(0).with_position(("center", "center"))
        puff_in_clip = clip.with_effects([Resize(lambda t: (2 * (LOGO_FLY - t) / LOGO_FLY) + 1)]).with_position(("center", "center")).with_duration(LOGO_FLY)
        stay_clip = clip.with_duration(LOGO_STAY).with_start(puff_in_clip.end).with_position(("center", "center"))
        puff_out_clip = clip.with_effects([Resize(lambda t: 2 * t / LOGO_FLY + 1)]).with_start(stay_clip.end).with_position(("center", "center")).with_duration(LOGO_FLY)

        return CompositeVideoClip([white_blank_image, puff_in_clip, stay_clip, puff_out_clip])

def is_video(path):
    return path.endswith('.mp4') or path.endswith('.avi') or path.endswith('.mov')
