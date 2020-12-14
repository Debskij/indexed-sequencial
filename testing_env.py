import string
from random import choice, randint

from consts import *
from database import database as db
from entry import IS_Database as IS_db
from record import record

alpha_r = [x * 0.1 for x in range(1, 11)]
beta_r = [x * 0.1 for x in range(1, 11)]


def command_generator(number: int) -> list:
    chars = string.ascii_letters + string.digits
    ret_list = []
    indexes = []
    for _ in range(number):
        command = choice(['a']) if len(indexes) else 'a'
        if command in ['d', 's']:
            idx = choice(indexes)
            del indexes[indexes.index(idx)]
            ret_list.append(f'{command} {idx}')
        elif command == 'a':
            value = ''.join((choice(chars) for _ in range(MAX_RECORD_LENGTH)))
            index = randint(1, (10 ** INDEX_LENGTH) - 1)
            ret_list.append(f'{command} {index} {value}')
            if index not in indexes:
                indexes.append(index)
        else:
            ret_list.append(f'{command}')
    return ret_list


def command_parser(idx_seq: IS_db, command: str):
    new_command = command.split(' ')
    if new_command[0] == 'a':
        idx_seq.add(record(int(new_command[1]), new_command[2]))
    elif new_command[0] == 'd':
        idx_seq.delete(int(new_command[1]))
    elif new_command[0] == 's':
        idx_seq.search(int(new_command[1]))
    elif new_command[0] == 'r':
        idx_seq.reorganise()


cmd = command_generator(1000)

paths = {
    "main": 'data/main',
    "main_reorganise": 'data/main_reorganise',
    "index": 'data/index',
    "overflow": 'data/overflow'
}
ans = []
for a in alpha_r:
    row_val = []
    for b in beta_r:

        new_database = db(page_file_path=paths.get('index'),
                          main_file_path=paths.get('main'),
                          overflow_area_path=paths.get('overflow'),
                          reorganise_main_file_path=paths.get('main_reorganise'),
                          block_size=4, page_utilization_factor=a, limit_of_overflow=b)

        idx_seq = IS_db(new_database)
        for command in cmd:
            command_parser(idx_seq, command)
        print(new_database.read_write_counter)
        row_val.append(new_database.read_write_counter)
    ans.append(row_val)

print(ans)