from editor import Editor
from event_analyzer import EventAnalyzer
from game import Game
import yaml
import os
import time
from utils import format_time
import argparse
import mark


def main():
    parser = argparse.ArgumentParser(
        description='足球导演 - 足球比赛视频分析与剪辑',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "action",
        type=str,
        choices=["preview", "make", "mark", "clean", "analyze"],
        help="""要执行的操作：

mark: 在原始比赛视频中标记事件
analyze: 根据比赛事件生成分析数据和解说文字（不创建视频）
preview: 预览比赛视频中配音解说的部分
make: 创建并保存比赛视频和集锦
clean: 删除该比赛生成的中间文件
""",
        metavar="action"
    )
    parser.add_argument(
        "game",
        type=str,
        help="比赛配置文件的路径（YAML格式）",
        metavar="game"
    )
    args = parser.parse_args()

    directory, filename = os.path.split(args.game)
    os.chdir(directory)
    game_id, ext = os.path.splitext(os.path.basename(filename))
    if ext not in ['.yaml', '.yml']:
        print(f"错误：{filename} 不是有效的游戏配置文件")
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
    elif args.action == "make":
        editor.edit()
        editor.save()
    elif args.action == "clean":
        confirm = input("确定要删除该比赛生成的文件吗？(y/n): ").lower()
        if confirm == "y":
            os.remove(f"game.{game.game_id}.mp4")
            os.remove(f"highlights.{game.game_id}.mp4")
            os.remove(f"logo.{game.game_id}.mp4")
            os.remove(f"game.{game.game_id}.pkl")
            print(f"Game {game.game_id} cleaned")
    elif args.action == "analyze":
        # no more action needed
        return 0
    else:
        print("unknown action:", args.action)
        return 1


    print(f"完成，用时{format_time(time.time() - start)}")
    time.sleep(2)


if __name__ == '__main__':
    main()