from editor import Editor
from voicer import Voicer
from comment_writer import CommentWriter
from event_detector import EventDetector
from match import Match
import yaml
import os
import sys
import time
from utils import format_time


def main():
    start = time.time()
    directory, filename = os.path.split(sys.argv[1])
    os.chdir(directory)
    match_id, ext = os.path.splitext(os.path.basename(filename))
    if ext not in ['.yaml', '.yml']:
        print(f"Error: {filename} is not a valid match file")
        return 1
        
    # read project yaml
    with open(filename, 'r', encoding='UTF-8') as f:
        match = Match(match_id, yaml.safe_load(f))
    
    editor = Editor(match)

    commentWriter = CommentWriter(match)
    commentWriter.create_comments()

    voicer = Voicer(match)
    voicer.make_voice()

    editor.edit(voicer)

    editor.save()

    print(f"Done in {format_time(time.time() - start)}")
    time.sleep(2)


if __name__ == '__main__':
    main()