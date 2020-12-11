from database import database
from record import record, page_index
from bisect import bisect


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
        page_no = self.db.find_page_by_key(value.index)
        page = self.db.load_page_from_main(page_no)
        if self.count_empty(page):
            page.append(value)
            page.sort(key=lambda rec: rec.index)
        else:
            idx = 0
            while len(page) > idx + 1 and value.index > page[idx + 1].index:
                idx += 1
            if not page[idx].pointer:
                page[idx].pointer = self.db.save_record_to_overflow(value)
            else:
                new_pointer = self.put_in_proper_place(page[idx].pointer, value)
                if new_pointer >= 0:
                    page[idx].pointer = new_pointer
                elif new_pointer == -2:
                    print(f'Record with index {value.index} already exists!')
                else:
                    return
        self.db.save_page_to_main(page_no, page)

    def put_in_proper_place(self, pointer: int, value: record):
        previous_pointer, previous_record = pointer, self.db.load_record_from_overflow(pointer)
        if previous_record > value:
            value.pointer = pointer
            return self.db.save_record_to_overflow(value)
        else:
            while previous_record.pointer and previous_record < value:
                new_record = self.db.load_record_from_overflow(previous_record.pointer)
                if new_record == value:
                    return -2
                if new_record > value:
                    value.pointer = previous_record.pointer
                    previous_record.pointer = self.db.save_record_to_overflow(value)
                    break
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
            possible_page[indexes.index(value.index)].is_deleted = True
            self.db.save_page_to_main(possible_page_no, possible_page)
        elif len(indexes) < self.db.block_size:  # index not existing
            return -1
        pointer_to_traverse = possible_page[bisect(indexes, value.index) - 1].pointer
        if pointer_to_traverse:
            record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse)
            while record_from_pointer.pointer and record_from_pointer < value:
                pointer_to_traverse = record_from_pointer.pointer
                record_from_pointer = self.db.load_record_from_overflow(pointer_to_traverse)
            if record_from_pointer == value:
                self.db.update_record_in_overflow(value, pointer_to_traverse)
            else:
                return -1
        else:
            return -1

    def count_empty(self, page: list) -> int:
        return len([record.empty for record in page])
