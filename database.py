import copy
from itertools import islice
from math import ceil
from bisect import bisect

from record import *

def page_printer(page: list):
    for rec in page:
        print(rec.write().rstrip('\n'))

def parse_pages(page_str: list) -> page_index:
    return page_index(int(page_str[0]), int(page_str[1]))


def parse_page_to_str(pages: list) -> list:
    return [page.write() for page in pages]


def parse_str_to_record(record_str: str) -> record:
    r = [x.strip() for x in record_str.split('\t')]
    try:
        return record(int(r[0]), r[1], int(r[2]), is_deleted=int(r[3]))
    except ValueError:
        return record(int(r[0]), r[1], is_deleted=int(r[3]))


def parse_file_page_to_records(records_list: list) -> list:
    return [parse_str_to_record(v_record) for v_record in records_list]


class database:
    def __init__(self, page_file_path: str, main_file_path: str, overflow_area_path: str,
                 block_size: int, page_utilization_factor: float, limit_of_overflow: float,
                 reorganise_main_file_path: str):
        self.paths = {
            "main": main_file_path,
            "index": page_file_path,
            "overflow": overflow_area_path,
            "reorganise": reorganise_main_file_path
        }

        self.index_file = open(page_file_path, 'r+')
        self.main_file = open(main_file_path, 'r+')
        self.overflow_file = open(overflow_area_path, 'r+')
        self.main_reorganise_file = open(reorganise_main_file_path, 'r+')

        self.file_names = {
            "main": self.main_file,
            "index": self.index_file,
            "overflow": self.overflow_file,
            "reorganise": self.main_reorganise_file
        }

        self.block_size = block_size
        self.alpha = page_utilization_factor
        self.pointer_chain = []
        self.pointer_chain_limit = 0
        self.limit_of_overflow = limit_of_overflow
        self.actual_invalid_records = 0
        self.actual_main_records = 0
        self.reorganising_buffer = []
        self.page_buffer = []
        self.reorganising_page_no = 0
        self.erase_file('all')
        self.create_guard_record(0)
        self.reload_files()
        self.read_pages()

    def create_guard_record(self, idx: int):
        guard_record = record(idx, 'guard')
        self.save_record_to_main_reorganise(guard_record)
        page_idx = self.reorganising_force_write_page()
        self.save_page_to_index_reorganise(page_idx)
        self.save_page_to_index()

    def reload_files(self):
        for file in self.file_names.values():
            file.flush()
            file.seek(0)

    def create_page_of_records(self, page=None):
        if page is None:
            page = list()
        page = page + [record(0, '') for _ in range(self.block_size - len(page))]
        return page

    def save_page_to_index(self):
        if len(self.page_buffer) > 0:
            for page_idx in self.page_buffer:
                self.index_file.write(page_idx.write())
                self.page_buffer = []

    def save_page_to_index_reorganise(self, page: page_index):
        self.page_buffer.append(page)
        if len(self.page_buffer) == self.block_size:
            self.save_page_to_index()

    def save_record_to_main_reorganise(self, value: record):
        if value.is_deleted:
            return None
        copy_of_value = copy.deepcopy(value)
        copy_of_value.pointer = None
        self.reorganising_buffer.append(copy_of_value)
        self.actual_main_records += 1
        if len(self.reorganising_buffer) >= self.block_size * self.alpha:
            return self.reorganising_force_write_page()

    def reorganising_force_write_page(self):
        if len(self.reorganising_buffer) > 0:
            self.reorganising_buffer += [record(0, '') for _ in range(self.block_size - len(self.reorganising_buffer))]
            self.reload_files()
            self.save_page_to_main(self.reorganising_page_no, self.reorganising_buffer)
            p_idx = page_index(self.reorganising_buffer[0].index, self.reorganising_page_no)
            self.reorganising_buffer = []
            self.reorganising_page_no += 1
            self.reload_files()
            return p_idx
        else:
            return None

    def create_enough_empty_pages(self):
        self.reload_files()
        pages_needed = ceil((self.actual_invalid_records + self.actual_main_records) / (self.block_size * self.alpha))
        for _ in range(pages_needed):
            self.main_file.writelines(parse_page_to_str(self.create_page_of_records()))

    def erase_file(self, which: str):
        file_dir = {
            "index": self.index_file,
            "main": self.main_file,
            "overflow": self.overflow_file,
            "reorganise": self.main_reorganise_file
        }
        if which == 'all':
            for file in file_dir.keys():
                file_dir.get(file).truncate(0)
        if which in file_dir.keys():
            file_dir.get(which).truncate(0)

    def check_for_reorganisation(self) -> bool:
        if self.actual_main_records*self.limit_of_overflow < self.actual_invalid_records:
            return True
        return False

    def swap_mains(self):
        self.main_file, self.main_reorganise_file = self.main_reorganise_file, self.main_file

    def read_pages(self):
        self.reload_files()
        pages = [page.rstrip('\n').split('\t') for page in self.index_file.readlines()]
        self.pages = [parse_pages(page) for page in pages]
        self.reload_files()

    def find_page_by_key(self, key: int) -> int:
        return bisect([x.index for x in self.pages], key)-1

    def load_page(self, page_no: int, source) -> list:
        self.reload_files()
        try:
            return [line for line in islice(source, page_no * self.block_size, (page_no + 1) * self.block_size)]
        except IndexError:
            return []

    def save_page_to_main(self, page_no: int, page_values: list):
        self.reload_files()
        d = self.main_file.readlines()
        page_values = parse_page_to_str(page_values + [record(0, '') for _ in
                                                       range(self.block_size - len(page_values))])
        self.reload_files()
        d[page_no * self.block_size:(page_no + 1) * self.block_size] = page_values
        self.main_file.writelines(d)
        self.reload_files()

    def load_page_from_overflow(self, pointer: int) -> list:
        which_page_of = self.find_out_page_from_overload(pointer)
        return self.load_page(which_page_of, self.overflow_file)

    def load_record_from_overflow(self, pointer: int, max_val: int) -> record:
        if self.pointer_chain_limit != max_val:
            self.pointer_chain_limit = max_val
            self.pointer_chain = []
        pointer_chain_indices = [x[0] for x in self.pointer_chain]
        if pointer in pointer_chain_indices:
            return self.pointer_chain[pointer_chain_indices.index(pointer)][1]
        loaded_page = parse_file_page_to_records(self.load_page_from_overflow(pointer))
        seeked_value = loaded_page[pointer % self.block_size]
        for idx, element in enumerate(loaded_page):
            if seeked_value < element.index <= max_val:
                pointer_of_element = (pointer//self.block_size)*self.block_size+idx
                self.pointer_chain.append((pointer_of_element, copy.deepcopy(element)))
        return seeked_value

    def load_page_from_main(self, page_no: int) -> list:
        return parse_file_page_to_records(self.load_page(page_no, self.main_file))

    def load_page_from_main_reorganise(self, page_no: int) -> list:
        return parse_file_page_to_records(self.load_page(page_no, self.main_reorganise_file))

    def find_out_page_from_overload(self, pointer: int) -> int:
        return pointer // self.block_size

    def update_record_in_overflow(self, value: record, pointer: int):
        page_of = self.load_page_from_overflow(pointer)
        page_of[pointer % self.block_size] = value.write()
        self.update_page_in_overflow(self.find_out_page_from_overload(pointer), page_of)

    def update_page_in_overflow(self, page_no: int, page: list):
        self.reload_files()
        d = self.overflow_file.readlines()
        d[page_no * self.block_size:(page_no + 1) * self.block_size] = page
        self.reload_files()
        self.overflow_file.writelines(d)
        self.reload_files()

    def save_record_to_overflow(self, value: record):
        self.reload_files()
        d = self.overflow_file.readlines()
        self.reload_files()
        d.append(value.write())
        self.actual_invalid_records += 1
        self.overflow_file.writelines(d)
        self.reload_files()
        return len(d) - 1

    def reload_file(self):
        self.main_file.flush()
