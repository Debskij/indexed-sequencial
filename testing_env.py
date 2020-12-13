import string
from random import choice, randint

from consts import *
from database import database as db
from entry import IS_Database as IS_db
from record import record

alpha_r = [x * 0.20 for x in range(1, 5)]
beta_r = [x * 0.20 for x in range(1, 5)]


def command_generator(number: int) -> list:
    chars = string.ascii_letters + string.digits
    ret_list = []
    for _ in range(number):
        value = ''.join((choice(chars) for _ in range(MAX_RECORD_LENGTH)))
        index = randint(1, (10 ** INDEX_LENGTH) - 1)
        ret_list.append(f'a {index} {value}')
    return ret_list

def command_parser(idx_seq: IS_db, command: str):
    new_command = command.split(' ')
    if new_command[0] == 'a':
        idx_seq.add(record(int(new_command[1]), new_command[2]))

cmd = command_generator(50)

paths = {
    "main": 'data/main',
    "main_reorganise": 'data/main_reorganise',
    "index": 'data/index',
    "overflow": 'data/overflow'
}

for a in alpha_r:
    for b in beta_r:

        new_database = db(page_file_path=paths.get('index'),
                          main_file_path=paths.get('main'),
                          overflow_area_path=paths.get('overflow'),
                          reorganise_main_file_path=paths.get('main_reorganise'),
                          block_size=4, page_utilization_factor=a, limit_of_overflow=b)

        idx_seq = IS_db(new_database)
        for command in cmd:
            command_parser(idx_seq, command)
            idx_seq.auto_reorganisation()
        print(new_database.read_write_counter)