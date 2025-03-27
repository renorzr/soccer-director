from moviepy import ImageClip, TextClip, CompositeVideoClip
from utils import format_time


class TextProp:
    def __init__(self, left, top, width, height, color=None, font=None):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.color = color
        self.font = font
    @classmethod
    def from_dict(cls, obj):
        return cls(obj['left'], obj['top'], obj['width'], obj['height'], color=obj.get('color'), font=obj.get('font')) if obj is not None else None

class Scoreboard:
    def __init__(self, img: str, texts: dict, textprops: dict):
        self.img = img
        self.texts = texts
        self.textprops = textprops


    @classmethod
    def from_dict(cls, texts, obj):
        textprops = {}
        img = 'scoreboard.png'
        for key, value in obj.items():
            if key == 'img':
                img = value
            else:
                textprops[key] = TextProp.from_dict(value)

        return cls(img, texts, textprops)


    def render(self, time, duration, score0, score1):
        clips = [
            ImageClip(self.img).with_duration(duration).with_start(0).with_position(("center", "top")),
            render_text(str(score0), self.textprops.get('score0'), 0, duration),
            render_text(str(score1), self.textprops.get('score1'), 0, duration),
        ]

        for key, text in self.texts.items():
            textprop = self.textprops.get(key)
            if textprop is not None:
                clips.append(render_text(text, textprop, 0, duration))
            
        clips = [c for c in clips if c is not None]

        time_textprop = self.textprops.get('time')
        if time_textprop is not None:
            for i in range(0, int(duration)):
                clips.append(render_text(format_time(time + i, 0), time_textprop, i, 1))

        return CompositeVideoClip(clips)



def render_text(text, textprop, time, duration):
    return TextClip(text=text, 
                    font=textprop.font or "ROGFonts-Regular_0.otf", 
                    color=textprop.color or 'white',
                    size=(textprop.width, textprop.height)) \
        .with_duration(duration).with_start(time).with_position((textprop.left, textprop.top)) \
            if textprop is not None else None


if __name__ == '__main__':
    font = 'SourceHanSansSC-Medium.otf'
    b = Scoreboard.from_dict(
        {
            'title': 'Soccer Match',
            'team0': '银杏',
            'team1': '樱花',
            'quarter': 'Q2',
        },
        {
        'img': '../soccer-demo/scoreboard.png',
        'quarter': {
            'left': 170,
            'top': 70,
            'width': 30,
            'height': 10,
        },
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
            'font': font
        },
        'team1': {
            'left': 230,
            'top': 30,
            'width': 70,
            'height': 25,
            'font': font
        },
        'time': {
            'left': 145,
            'top': 30,
            'width': 65,
            'height': 20,
        },
    })

    b.render(60, 10, 0, 0).preview()