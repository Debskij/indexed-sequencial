from consts import *
import re

class record:
    def __init__(self, idx: int, value: str, pointer=None):
        self.index = idx
        self.value = value
        self.pointer = pointer
        self.is_deleted = False
        self.empty = bool(not idx and re.compile('^0+$').match(self.value) and not pointer)

    def write(self):
        return f'{str(self.index).zfill(INDEX_LENGTH)}\t{self.value.center(MAX_RECORD_LENGTH)}\t{self.pointer.zfill(POINTER_LENGTH)}'

    def set_pointer(self, pointer: int):
        self.pointer = pointer

    def __lt__(self, other):
        if type(other) == int:
            return self.index < other
        if type(other) == record:
            return self.index < other.index

    def __gt__(self, other):
        if type(other) == int:
            return self.index > other
        if type(other) == record:
            return self.index > other.index


class page_index:
    def __init__(self, idx: int, page_no: int):
        self.index = idx
        self.page_no = page_no

    def write(self):
        return f'{str(self.index).zfill(INDEX_LENGTH)}\t{str(self.page_no).zfill(MAX_PAGE_LENGTH)}'
