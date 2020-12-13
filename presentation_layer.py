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
    (1, 'test'),
    (3, 'test'),
    (5, 'test'),
    (15, 'test'),
    (6, 'test'),
    (8, 'test'),
]
for v_record in records_testing:
    r = record(v_record[0], v_record[1])
    program.add(r)
    program.auto_reorganisation()
program.update(record(5, 'testtest'))
program.delete(3)
program.delete(15)
page0 = program.view_all_pages()
for rec in page0:
    print(rec)
print(program.search(5))
print(program.search(9))
# program.reorganise()
# program.add(record(12, 'test'))
# program.delete(2)
# program.delete(3)
# print(new_database.actual_invalid_records, new_database.actual_main_records)
# program.reorganise()
