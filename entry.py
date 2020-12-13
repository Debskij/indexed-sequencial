import copy
from bisect import bisect

from consts import INDEX_LENGTH
from database import database
from record import record


def count_empty(page: list) -> int:
    for key, v_rc in enumerate(page):
        if v_rc.empty:
            return key
    return -1


def page_printer(page: list):
    for rec in page:
        print(rec.write().rstrip('\n'))


class IS_Database:
    def __init__(self, db: database):
        self.db = db

    def commands(self, command: str, value=None):
        return {
            "add": self.add,
            "delete": self.delete,
            "reorganise": self.reorganise,
            "update": self.update,
            "search": self.search,
        }.get(command).__call__(value)

    def add(self, value: record):
        self.db.reload_files()
        page_no = self.db.find_page_by_key(value.index)
        page = self.db.load_page_from_main(page_no)
        self.db.reload_files()
        empty_idx = count_empty(page)
        if empty_idx >= 0:
            page[empty_idx] = value
            page = sorted(page)
            self.db.actual_main_records += 1
        else:
            idx = 0
            while len(page) > idx + 1 and value.index > page[idx + 1].index:
                idx += 1
            if page[idx].pointer is None:
                page[idx].pointer = self.db.save_record_to_overflow(value)
            else:
                new_pointer = self.put_in_proper_place(page[idx].pointer, value)
                if new_pointer >= 0:
                    page[idx].pointer = new_pointer
                elif new_pointer == -2:
                    print(f'Record with index {value.index} already exists!')
                    return
                else:
                    return
        self.db.save_page_to_main(page_no, page)

    def put_in_proper_place(self, pointer: int, value: record):
        previous_pointer, previous_record = pointer, self.db.load_record_from_overflow(pointer, value.index)
        if previous_record > value:
            value.pointer = pointer
            return self.db.save_record_to_overflow(value)
        elif previous_record.pointer is None:
            previous_record.pointer = self.db.save_record_to_overflow(value)
            self.db.update_record_in_overflow(previous_record, previous_pointer)
            return -1
        else:
            while previous_record.pointer is not None and previous_record < value:
                new_record = self.db.load_record_from_overflow(previous_record.pointer, value.index)
                if new_record == value:
                    if new_record.is_deleted:
                        value.pointer = new_record.pointer
                        self.db.update_record_in_overflow(value, previous_record.pointer)
                        return -1
                    else:
                        return -2
                if new_record > value:
                    value.pointer = previous_record.pointer
                    previous_record.pointer = self.db.save_record_to_overflow(value)
                    self.db.update_record_in_overflow(previous_record, previous_pointer)
                    return -1
                if not new_record.pointer:
                    new_record.pointer = self.db.save_record_to_overflow(value)
                    self.db.update_record_in_overflow(new_record, previous_record.pointer)
                    return -1
                previous_pointer, previous_record = previous_record.pointer, new_record
            return -1

    def delete(self, key: int):
        possible_page_no = self.db.find_page_by_key(key)
        possible_page = self.db.load_page_from_main(possible_page_no)
        indexes = [e_record.index for e_record in possible_page if not e_record.empty]
        if key in indexes:  # index in main area
            possible_page[indexes.index(key)].is_deleted = True
            self.db.actual_main_records -= 1
            self.db.save_page_to_main(possible_page_no, possible_page)
            self.db.reload_files()
            return -1
        elif len(indexes) < self.db.block_size:  # index not existing
            return -1
        pointer_to_traverse = possible_page[bisect(indexes, key) - 1].pointer
        if pointer_to_traverse:
            record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse, key)
            while record_from_pointer.pointer is not None and record_from_pointer < key:
                pointer_to_traverse = record_from_pointer.pointer
                record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse, key)
            if record_from_pointer.index == key:
                record_from_pointer.is_deleted = True
                self.db.actual_invalid_records -= 1
                self.db.update_record_in_overflow(record_from_pointer, pointer_to_traverse)
            else:
                return -1
        else:
            return -1

    def update(self, value: record):
        possible_page_no = self.db.find_page_by_key(value.index)
        possible_page = self.db.load_page_from_main(possible_page_no)
        indexes = [e_record.index for e_record in possible_page if not e_record.empty]
        if value.index in indexes:  # index in main area
            idx_in_page = indexes.index(value.index)
            if not possible_page[idx_in_page].is_deleted:
                value.pointer = possible_page[idx_in_page].pointer
                possible_page[idx_in_page] = value
                self.db.save_page_to_main(possible_page_no, possible_page)
        elif len(indexes) < self.db.block_size:  # index not existing
            return -1
        pointer_to_traverse = possible_page[bisect(indexes, value.index) - 1].pointer
        if pointer_to_traverse:
            record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse, value.index)
            while record_from_pointer.pointer and record_from_pointer < value:
                pointer_to_traverse = record_from_pointer.pointer
                record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse, value.index)
            if record_from_pointer == value and not record_from_pointer.is_deleted:
                value.pointer = record_from_pointer.pointer
                self.db.update_record_in_overflow(value, pointer_to_traverse)
            else:
                return -1
        else:
            return -1

    def reorganise(self):
        self.db.erase_file('reorganise')
        self.db.swap_mains()
        self.db.erase_file('index')
        self.db.create_enough_empty_pages()
        number_of_pages = int(self.db.reorganising_page_no)
        self.db.actual_main_records = 0
        self.db.reload_files()
        self.db.reorganising_page_no = 0
        page_no = 0
        while page_no < number_of_pages:
            record_page = self.db.load_page_from_main_reorganise(page_no)
            record_page = [v_record for v_record in record_page if not v_record.empty]
            idx = 0
            while idx < len(record_page):
                page_idx = self.db.save_record_to_main_reorganise(record_page[idx])
                limit = record_page[idx + 1] if idx < len(record_page) - 1 else 10 ** INDEX_LENGTH
                if page_idx:
                    self.db.save_page_to_index_reorganise(page_idx)
                if record_page[idx].pointer is not None:
                    rc_overflow = self.db.load_record_from_overflow(record_page[idx].pointer, limit)
                    page_idx = self.db.save_record_to_main_reorganise(rc_overflow)
                    if page_idx:
                        self.db.save_page_to_index_reorganise(page_idx)
                    while rc_overflow.pointer is not None:
                        rc_overflow = self.db.load_record_from_overflow(rc_overflow.pointer, limit)
                        page_idx = self.db.save_record_to_main_reorganise(rc_overflow)
                        if page_idx:
                            self.db.save_page_to_index_reorganise(page_idx)
                idx += 1
            page_no += 1
        page_idx = self.db.reorganising_force_write_page()
        if page_idx:
            self.db.save_page_to_index_reorganise(page_idx)
        self.db.erase_file('overflow')
        self.db.erase_file('reorganise')
        self.db.actual_invalid_records = 0
        self.db.reload_files()
        self.db.save_page_to_index()
        self.db.read_pages()

    def search(self, key: int):
        possible_page_no = self.db.find_page_by_key(key)
        possible_page = self.db.load_page_from_main(possible_page_no)
        indexes = [e_record.index for e_record in possible_page if not e_record.empty]
        possible_place = bisect(indexes, key) - 1
        if key in indexes:  # index in main area
            location = indexes.index(key)
            right_value = possible_page[location]
            if right_value.is_deleted:
                return None
            return f'MAIN\nPAGE: {possible_page_no}\nPOSITION: {location}\nINDEX: {key}\n' \
                   f'VALUE: {right_value.value}\n'
        elif possible_page[possible_place].pointer is not None:
            if len(indexes) - 1 <= possible_place:
                limit = 10 ** INDEX_LENGTH
            else:
                limit = indexes[possible_place + 1]
            new_record_pointer = possible_page[possible_place].pointer
            new_record = self.db.load_record_from_overflow(new_record_pointer, limit)
            if new_record.index == key and not new_record.is_deleted:
                return f'OVERFLOW\nPAGE: {new_record_pointer // self.db.block_size}' \
                       f'\nPOSITION: {new_record_pointer - (new_record_pointer // self.db.block_size) * self.db.block_size}' \
                       f'\nINDEX: {key}\nVALUE: {new_record.value}'
            while new_record.pointer is not None and new_record.index < key:
                new_record_pointer = new_record.pointer
                new_record = self.db.load_record_from_overflow(new_record_pointer, limit)
                if new_record.index == key and not new_record.is_deleted:
                    return f'OVERFLOW\nPAGE: {new_record_pointer // self.db.block_size}' \
                           f'\nPOSITION: {new_record_pointer - (new_record_pointer // self.db.block_size) * self.db.block_size}' \
                           f'\nINDEX: {key}\nVALUE: {new_record.value}'
        return f'RECORD WITH KEY: {key} NOT FOUND'

    def view_page(self, page_no: int):
        page = [x for x in self.db.load_page_from_main(page_no)]
        empty = len([x for x in page if x.empty])
        deleted = 0
        page = [x for x in page if not x.empty]
        ret_page = []
        main_ptr = 0
        while main_ptr < len(page):
            limit = page[main_ptr + 1] if main_ptr < len(page) - 1 else 10 ** INDEX_LENGTH
            if not page[main_ptr].is_deleted:
                if page[main_ptr].index > 0:
                    ret_page.append(page[main_ptr])
            else:
                deleted += 1
            if page[main_ptr].pointer is not None:
                next_record = self.db.load_record_from_overflow(page[main_ptr].pointer, limit)
                if not next_record.is_deleted:
                    ret_page.append(copy.deepcopy(next_record))
                else:
                    deleted += 1
                while next_record.pointer is not None:
                    next_record = self.db.load_record_from_overflow(next_record.pointer, limit)
                    if not next_record.is_deleted:
                        ret_page.append(copy.deepcopy(next_record))
                    else:
                        deleted += 1
            main_ptr += 1
        return [f'PAGE NO. {page_no}. EMPTY PLACES: {empty}. DELETED RECORDS: {deleted}'] + [page.write().rstrip('\n')
                                                                                             for page in ret_page]

    def view_all_pages(self):
        page_count = self.db.reorganising_page_no
        return [x for page_no in range(page_count) for x in self.view_page(page_no)]

    def auto_reorganisation(self):
        if self.db.check_for_reorganisation():
            self.db.reload_files()
            self.reorganise()
