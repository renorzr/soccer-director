from moviepy import ImageClip, TextClip, CompositeVideoClip

class TextProp:
    def __init__(self, left, top, width, height, color=None):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.color = color

    @classmethod
    def from_dict(cls, obj):
        return cls(obj['left'], obj['top'], obj['width'], obj['height'], obj.get('color')) if obj is not None else None

class Scoreboard:
    def __init__(self, img: str, title: str, team0: str, team1: str, title_textprop: TextProp, time_textprop: TextProp, team0_textprop: TextProp, team1_textprop: TextProp, score0_textprop: TextProp, score1_textprop: TextProp):
        self.img = img
        self.title = title
        self.team0 = team0
        self.team1 = team1
        self.title_textprop = title_textprop
        self.time_textprop = time_textprop
        self.team0_textprop = team0_textprop
        self.team1_textprop = team1_textprop
        self.score0_textprop = score0_textprop
        self.score1_textprop = score1_textprop


    @classmethod
    def from_dict(cls, title, team0, team1, obj):
        return cls(
            obj['img'], title, team0, team1,
            TextProp.from_dict(obj.get('title')), TextProp.from_dict(obj.get('time')),
            TextProp.from_dict(obj.get('team0')), TextProp.from_dict(obj.get('team1')),
            TextProp.from_dict(obj.get('score0')), TextProp.from_dict(obj.get('score1'))
        )


    def render(self, time, duration, score0, score1):
        clips = [
            ImageClip(self.img).with_duration(duration).with_start(0).with_position(("center", "top")),
            render_text(self.title, self.title_textprop, 0, duration),
            render_text(self.team0, self.team0_textprop, 0, duration),
            render_text(self.team1, self.team1_textprop, 0, duration),
            render_text(str(score0), self.score0_textprop, 0, duration),
            render_text(str(score1), self.score1_textprop, 0, duration)
        ]
        clips = [c for c in clips if c is not None]

        if self.time_textprop is not None:
            for i in range(0, duration):
                clips.append(render_text(format_time(time + i), self.time_textprop, i, 1))

        return CompositeVideoClip(clips)


def format_time(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f'{minutes:02}:{seconds:02}'


def render_text(text, textprop, time, duration):
    return TextClip(text=text, 
                    font="ROGFonts-Regular_0.otf", 
                    color=textprop.color or 'white',
                    size=(textprop.width, textprop.height)) \
        .with_duration(duration).with_start(time).with_position((textprop.left, textprop.top)) \
            if textprop is not None else None


if __name__ == '__main__':
    b = Scoreboard.from_dict(
        'Soccer Match',
        'GNK',
        'SKR',
        {
        'img': '../soccer-demo/scoreboard.png',
        'score0': {
            'left': 12,
            'top': 32,
            'width': 20,
            'height': 20,
        },
        'score1': {
            'left': 327,
            'top': 32,
            'width': 18,
            'height': 18,
        },
        'team0': {
            'left': 50,
            'top': 30,
            'width': 70,
            'height': 25,
        },
        'team1': {
            'left': 230,
            'top': 30,
            'width': 70,
            'height': 25,
        },
        'time': {
            'left': 145,
            'top': 30,
            'width': 65,
            'height': 20,
        },
    })

    b.render(60, 10, 0, 0).preview()