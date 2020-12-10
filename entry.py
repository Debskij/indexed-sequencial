from database import database
from record import record, page_index


class IS_Database:
    def __init__(self, db: database):
        self.db = db

    def commands(self, command, value):
        return {
            "add": self.add,
            "delete": self.delete,
            "reorganise": self.reorganise,
            "update": self.update,
        }.get(command)(value)

    def add(self, value: record):
        page_no = self.db.find_page(value.index)
        page = self.db.load_page_from_main(page_no)
        if self.count_empty(page):
            page.append(value)
            page.sort(key=lambda rec: rec.index)
        else:
            idx = 0
            while len(page) > idx + 1 and value.index > page[idx+1].index:
                idx += 1
            if not page[idx].pointer:
                page[idx].pointer = self.db.save_record_to_overflow(value)
            else:
                new_pointer = self.put_in_proper_place(page[idx].pointer, value)
                if new_pointer != -1:
                    page[idx].pointer = new_pointer
                else:
                    return
        self.db.save_page_to_main(page_no, page)

    def put_in_proper_place(self, pointer: int, value: record):
        previous_pointer, previous_record = pointer, self.db.get_record_from_overflow(pointer)
        if previous_record > value:
            value.pointer = pointer
            return self.db.save_record_to_overflow(value)
        else:
            while previous_record.pointer and previous_record < value:
                new_record = self.db.get_record_from_overflow(previous_record.pointer)
                if new_record > value:
                    value.pointer = previous_record.pointer
                    previous_record.pointer = self.db.save_record_to_overflow(value)
                    break
                previous_pointer, previous_record = previous_record.pointer, new_record
            return -1

    def count_empty(self, page: list) -> int:
        return len([record.empty for record in page])