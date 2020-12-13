from database import database as db
from entry import IS_Database as is_db
from record import record

paths = {
    "main" : 'data/main',
    "main_reorganise" : 'data/main_reorganise',
    "index" : 'data/index',
    "overflow" : 'data/overflow'
}

new_database = db(page_file_path=paths.get('index'),
                  main_file_path=paths.get('main'),
                  overflow_area_path=paths.get('overflow'),
                  reorganise_main_file_path=paths.get('main_reorganise'),
                  block_size=4, page_utilization_factor=0.5, limit_of_overflow=0.3)

program = is_db(new_database)

records_testing = [
    (1, 'dupa'),
    (3, 'dupa'),
    (5, 'dupa'),
    (7, 'dupa'),
    (9, 'dupa'),
    (11, 'dupa'),
    (2, 'dupa'),
]
for v_record in records_testing:
    r = record(v_record[0], v_record[1])
    program.add(r)
