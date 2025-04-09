from event import EventType
from moviepy import VideoFileClip
from utils import format_time

GOAL_BEFORE = 5
GOAL_AFTER = 7

def create_goal_clips(game):
    goal_events = [e for e in game.events if e.type == EventType.Goal]
    game_clip = VideoFileClip(f'game.{game.game_id}.mp4')
    for event in goal_events:
        goal_clip = game_clip.subclipped(event.time - GOAL_BEFORE, event.time + GOAL_AFTER)
        time = format_time(event.time, 0, False)
        team = game.teams[event.team]
        player = event.player or 'NA'
        goal_clip.write_videofile(f'goal-{game.game_id}-{time}-{team.name}-{player}.mp4', threads=32, fps=24)

