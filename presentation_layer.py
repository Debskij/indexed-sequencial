from database import database as db
from entry import IS_Database as isdb
from record import record

paths = {
    "main": 'data/main',
    "main_reorganise": 'data/main_reorganise',
    "index": 'data/index',
    "overflow": 'data/overflow'
}

new_database = db(page_file_path=paths.get('index'),
                  main_file_path=paths.get('main'),
                  overflow_area_path=paths.get('overflow'),
                  reorganise_main_file_path=paths.get('main_reorganise'),
                  block_size=4, page_utilization_factor=0.5, limit_of_overflow=0.3)


def pretty_printer(big_bad_list: list):
    for another_wolf in big_bad_list:
        print(another_wolf)


program = isdb(new_database)

testing = open('test-file').readlines()
for line in testing:
    command_line = line.rstrip('\n').split(' ')
    if command_line[0] in ['add', 'update', 'delete', 'search', 'view', 'reorganise']:
        ans = -3
        if command_line[0] in ['add', 'update'] and len(command_line) >= 3:
            try:
                command_line[1] = int(command_line[1])
            except ValueError:
                print(f'Invalid command passed in {line}')
                break
            ans = program.commands(command_line[0], record(command_line[1], command_line[2]))
        elif command_line[0] in ['delete', 'search', 'view'] and len(command_line) >= 2:
            if command_line[:2] == ['view', 'all']:
                ans = program.commands(''.join(command_line[:2]))
            try:
                command_line[1] = int(command_line[1])
            except ValueError:
                print(f'Invalid command passed in {line}')
                break
            ans = program.commands(command_line[0], command_line[1])
        else:
            ans = program.commands(command_line[0])
        possible_ans = {
            -2: 'failure!',
            -1: 'success',
            0: 'idk',
        }
        if type(ans) is not list and ans in possible_ans.keys():
            print(f'{command_line[0]} status: {possible_ans.get(ans)}')
        elif type(ans) is list:
            pretty_printer(ans)
        else:
            print(ans)
