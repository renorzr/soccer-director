from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip
from moviepy.video.fx import MultiplySpeed, Resize, FadeIn, FadeOut

DELAY_BEFORE_REPLAY = 4
REPLAY_BUFFER = 2

class Editor:
    def __init__(self, match):
        self.match = match
        self.clips = []
        self.main_video = VideoFileClip(self.match.main_video)
        self.logo_video = VideoFileClip(self.match.logo_video).with_effects([Resize(self.main_video.size)])

    def create_replays(self):
        # pick most important events
        events = [e for e in self.match.events if e.level >= 8]

        logo_video_duration = self.logo_video.duration

        last_main_time = 0
        for event in events:
            main_clip_before = self.main_video.subclipped(last_main_time, event.end + DELAY_BEFORE_REPLAY + logo_video_duration / 2).with_start(last_main_time)
            logo_clip_before = self.logo_video.with_start(main_clip_before.end - logo_video_duration / 2)
            replay_clip = self.main_video.subclipped(event.start - REPLAY_BUFFER, event.end + REPLAY_BUFFER).without_audio().with_effects([MultiplySpeed(0.5), FadeIn(0.5), FadeOut(0.5)]).with_start(main_clip_before.end)
            logo_clip_after = self.logo_video.with_start(replay_clip.end - logo_video_duration / 2)
            last_main_time = last_main_time + main_clip_before.duration + replay_clip.duration
            replay_clip.audio = self.main_video.audio.subclipped(replay_clip.start, replay_clip.end).with_start(replay_clip.start)

            self.clips.append(main_clip_before)
            self.clips.append(logo_clip_before)
            self.clips.append(replay_clip)
            self.clips.append(logo_clip_after)

        main_clip_after = self.main_video.subclipped(last_main_time, self.main_video.duration).with_start(last_main_time)
        self.clips.append(main_clip_after)
            
    def add_comment_voices(self, voicer):
        for comment in self.match.comments:
            voice_path = voicer.get_voice(comment)
            voice_clip = AudioFileClip(voice_path)
            self.clips.append(voice_clip.with_start(comment.time))

    def save(self, start=0, end=None):
        final_clip = self.composite()
        final_clip.write_videofile('output.mp4')

    def preview(self, start=0, end=None):
        final_clip = self.composite(start, end)
        final_clip.preview()

    def composite(self, start=0, end=None):
        final_clip = CompositeVideoClip(self.clips)

        if not end:
            return final_clip

        print(f"Subclipping from {start} to {end}")
        return final_clip.subclipped(start, end)


    def get_frame(self, time):
        return self.main_video.get_frame(time)

    def get_duration(self):
        return self.main_video.duration