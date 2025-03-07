from editor import Editor
from voicer import Voicer
from comment_writer import CommentWriter
from event_detector import EventDetector
from match import Match
import yaml
import os
import sys
import time


def main():
    # change work dir if specified in command line
    if len(sys.argv) > 1:
        os.chdir(sys.argv[1])
        
    # read project yaml
    with open('match.yaml', 'r', encoding='UTF-8') as f:
        match = Match(yaml.safe_load(f))
    
    editor = Editor(match)

    eventDetector = EventDetector(match, editor)
    eventDetector.detect()

    commentWriter = CommentWriter(match)
    commentWriter.create_comments()

    #voicer = Voicer(match)
    #voicer.make_voice()

    editor.edit()

    editor.save()

    time.sleep(1)
    print('Done!')


if __name__ == '__main__':
    main()