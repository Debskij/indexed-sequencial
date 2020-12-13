from database import database
from record import record
from bisect import bisect


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
        previous_pointer, previous_record = pointer, self.db.load_record_from_overflow(pointer)
        if previous_record > value:
            value.pointer = pointer
            return self.db.save_record_to_overflow(value)
        elif previous_record.pointer is None:
            previous_record.pointer = self.db.save_record_to_overflow(value)
            self.db.update_record_in_overflow(previous_record, previous_pointer)
            return -1
        else:
            while previous_record.pointer is not None and previous_record < value:
                new_record = self.db.load_record_from_overflow(previous_record.pointer)
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
        indexes = [e_record.index for e_record in possible_page if not e_record.is_empty]
        if key in indexes:  # index in main area
            possible_page[indexes.index(key)].is_deleted = True
            self.db.save_page_to_main(possible_page_no, possible_page)
        elif len(indexes) < self.db.block_size:  # index not existing
            return -1
        pointer_to_traverse = possible_page[bisect(indexes, key) - 1].pointer
        if pointer_to_traverse:
            record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse)
            while record_from_pointer.pointer and record_from_pointer < key:
                pointer_to_traverse = record_from_pointer.pointer
                record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse)
            if record_from_pointer == key:
                record_from_pointer.is_deleted = True
                self.db.update_record_in_overflow(record_from_pointer, pointer_to_traverse)
            else:
                return -1
        else:
            return -1

    def update(self, value: record):
        possible_page_no = self.db.find_page_by_key(value.index)
        possible_page = self.db.load_page_from_main(possible_page_no)
        indexes = [e_record.index for e_record in possible_page if not e_record.is_empty]
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
            record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse)
            while record_from_pointer.pointer and record_from_pointer < value:
                pointer_to_traverse = record_from_pointer.pointer
                record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse)
            if record_from_pointer == value and not record_from_pointer.is_deleted:
                value.pointer = record_from_pointer.pointer
                self.db.update_record_in_overflow(value, pointer_to_traverse)
            else:
                return -1
        else:
            return -1

    def reorganise(self):
        self.db.swap_mains()
        self.db.erase_file('index')
        page_no = 0
        while True:
            record_page = self.db.load_page_from_main_reorganise(page_no)
            record_page = [v_record for v_record in record_page if not v_record.empty]
            if not len(record_page):
                break
            idx = 0
            while idx < len(record_page):
                page_idx = self.db.save_record_to_main_reorganise(record_page[idx])
                if page_idx:
                    self.db.save_page_to_index_reorganise(page_idx)
                if record_page[idx].pointer:
                    rc_overflow = self.db.load_record_from_overflow(record_page[idx].pointer)
                    page_idx = self.db.save_record_to_main_reorganise(rc_overflow)
                    if page_idx:
                        self.db.save_page_to_index_reorganise(page_idx)
                    while rc_overflow.pointer:
                        rc_overflow = self.db.load_record_from_overflow(rc_overflow.pointer)
                        page_idx = self.db.save_record_to_main_reorganise(rc_overflow)
                        if page_idx:
                            self.db.save_page_to_index_reorganise(page_idx)
            page_idx = self.db.reorganising_force_write_page()
            if page_idx:
                self.db.save_page_to_index_reorganise(page_idx)
            self.db.save_page_to_index()