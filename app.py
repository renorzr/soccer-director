from editor import Editor
from event_analyzer import EventAnalyzer
from game import Game
import yaml
import os
import sys
import time
from utils import format_time
import argparse
import mark


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", type=str)
    parser.add_argument("game", type=str)
    args = parser.parse_args()

    directory, filename = os.path.split(args.game)
    os.chdir(directory)
    game_id, ext = os.path.splitext(os.path.basename(filename))
    if ext not in ['.yaml', '.yml']:
        print(f"Error: {filename} is not a valid game file")
        return 1
        
    # read project yaml
    with open(filename, 'r', encoding='UTF-8') as f:
        game = Game(game_id, yaml.safe_load(f))
    
    if args.action == "mark":
        mark.mark(game.main_video, f'events.{game_id}.csv')
        return 1

    editor = Editor(game)

    analyzer = EventAnalyzer(game)
    analyzer.analyze()

    start = time.time()
    if args.action == "preview":
        editor.preview()
    elif args.action == "output":
        editor.edit()
        editor.save()
    else:
        print("unknown action:", args.action)
        return 1


    print(f"Done in {format_time(time.time() - start)}")
    time.sleep(2)


if __name__ == '__main__':
    main()