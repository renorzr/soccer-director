import winsound
import sys
import vlc
import keyboard
import time
from utils import format_time
from event import Event, EventType, Tag

MOVE_TIME = 5
TAG_BUFFER_TIME = 2


def mark(video_path, events_file='events.csv'):
    # 初始化播放器
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    
    # 读取最后一个事件，并定位到该时间点
    events = Event.load_from_csv(events_file)
    last_event = max(events, key=lambda x: x.time) if events else None

    # 创建虚拟窗口（适用于无界面环境）
    if 'linux' in sys.platform:
        player.set_xwindow(0)
    elif 'win' in sys.platform:
        player.set_hwnd(0)
    
    player.play()
    if last_event:
        print('last event:', last_event)
        print('last event.time:', last_event.time)
        player.set_time(int(last_event.time * 1000))
    
    print("操作说明：")
    print("- 按 SPACE 打标")
    print("- 按 Q 停止播放并保存结果")
    print("- 按 P 暂停/恢复播放")
    print("- 按 左箭头 回退")
    print("- 按 右箭头 前进")

    tag_time = None
    while True:
        # 获取当前播放时间（秒）
        current_time = player.get_time() / 1000.0
        
        # 键盘监听
        if keyboard.is_pressed(' '):
            tag_time = current_time
            print("预备打标")
            winsound.Beep(1500, 200)
            time.sleep(0.3)  # 防抖

        if tag_time and current_time >= tag_time + TAG_BUFFER_TIME:
            player.pause()
            # 切换焦点
            keyboard.press_and_release('alt+tab')
            event = input_event(tag_time)
            keyboard.press_and_release('alt+tab')
            tag_time = None
            player.play()

            if event is None:
                print("取消打标")
                continue
            
            events.append(event)

            print(events)
            # 保存结果
            Event.save_to_csv(events_file, events)

        if keyboard.is_pressed('c'):
            print("取消打标")
            tag_time = None
            time.sleep(0.3)
    
        # 暂停
        if keyboard.is_pressed('p'):
            player.pause()
            time.sleep(0.3)

        # 停止
        if keyboard.is_pressed('q'):
            break

        # 回退
        if keyboard.is_pressed('left'):
            player.set_time(int((current_time - MOVE_TIME) * 1000))
            time.sleep(0.3)

        # 前进
        if keyboard.is_pressed('right'):
            player.set_time(int((current_time + MOVE_TIME) * 1000))
            time.sleep(0.3)

        time.sleep(0.01)  # 降低CPU占用

    player.stop()

def input_event(tag_time):
    args = {}
    t = format_time(tag_time)
    while True:
        print(f"Input event at {t}")
        args['time'] = t
        for field in Event.HEADERS[2:]:
            if field == 'type':
                event_type_str = input_choices("event type:", [e.name for e in EventType], [e.event_name for e in EventType])
                if event_type_str is None:
                    return None
                args['type'] = event_type_str
            elif field == 'tags':
                default_tags = ','.join([t.name for t in EventType[event_type_str].default_tags])
                if default_tags:
                    print('default tags:', default_tags)
                args[field] = input_choices("tags:", [t.name for t in Tag]) or default_tags
            else:
                input_event_field(args, field)

        event = Event.from_dict(args)
        print(event)

        while True:
            confirm = input("确认？([Y]es/[n]o/[c]ancel)").upper()
            if confirm == "Y" or confirm == "":
                return event
            elif confirm == "N":
                print("Input again")
                break
            elif confirm == "C":
                return None


def input_event_field(event, field):
    print(f"Input {field}{'(' + event[field] + ')' if event.get(field) else ''}:")
    event[field] = input() or event.get(field)


def input_choices(prompt, choices, displays=None):
    menu_line = ""
    for i, name in enumerate(displays or choices):
        menu_line += f" {i + 1}: {name}"

    try:
        input_str = input(prompt + menu_line + ' 0. 放弃: ')
        if input_str == '0':
            return None
        elif input_str == '':
            return ''
        return ','.join([str(choices[int(s) - 1]) for s in input_str.split(',')])
    except:
        print('Invalid choice')
        return input_choices(prompt, choices)
    

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("请指定视频路径：python script.py <视频文件路径>")
        sys.exit(1)
    
    mark(sys.argv[1])