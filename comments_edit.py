import pickle
from utils import format_time, parse_time


def edit(filename):
    with open(filename, 'rb') as f:
        game_data = pickle.load(f)

    print('Comments:')
    for i, comment in enumerate(game_data['comments']):
        print(f"{i:02d}", format_time(comment.time), comment.text)

    while True:
        choice = input("choose comment to edit (q to exit):")
        if choice == 'q':
            break
        
        try:
            index = int(choice)
            comment = game_data['comments'][index]
        except:
            continue
        
        print(f"{index:02d}", format_time(comment.time), comment.text)
        time = parse_time(input("time:"))
        text = input("text:")

        if not time and not text:
            print('canceled')
            continue

        if time:
            comment.time = time
        if text:
            comment.text = text

        print(f"{index:02d}", format_time(comment.time), comment.text)
        confirm = input("Save? (Yes/No)").upper()

        if confirm == "Y":
            game_data['comments'][index] = comment
            with open(filename, 'wb') as f:
                pickle.dump(game_data, f)



if __name__ == '__main__':
    import sys
    edit(sys.argv[1])