from itertools import islice

from record import *

from math import ceil

def parse_pages(page_str: list) -> page_index:
    return page_index(int(page_str[0]), int(page_str[1]))


def parse_page_to_str(pages: list) -> list:
    return [page.write() for page in pages]


def parse_str_to_record(record_str: str) -> record:
    r = [x.strip() for x in record_str.split(' ')]
    try:
        return record(int(r[0]), r[1], int(r[2]))
    except ValueError:
        return record(int(r[0]), r[1])


def parse_file_page_to_records(records_list: list) -> list:
    return [parse_str_to_record(v_record) for v_record in records_list]


class database:
    def __init__(self, page_file_path: str, main_file_path: str, overflow_area_path: str,
                 block_size: int, page_utilization_factor: float, limit_of_overflow: float,
                 records_on_page: int, reorganise_main_file: str):
        self.index_file = open(page_file_path, 'r+')
        self.main_file = open(main_file_path, 'r+')
        self.overflow_file = open(overflow_area_path, 'r+')
        self.main_reorganise_file = open(reorganise_main_file, 'r+')
        self.block_size = block_size
        self.alpha = page_utilization_factor
        self.limit_of_overflow = limit_of_overflow
        self.records_on_page = records_on_page
        self.actual_invalid_records = 0
        self.actual_main_records = 1
        self.reorganising_buffer = []
        self.reorganising_page_no = 0
        self.read_pages()

    def create_page_of_records(self, page=None):
        if page is None:
            page = list()
        page = page + [record(0, '') for _ in range(self.block_size - len(page))]
        return page

    def save_page_to_index(self, page: list):
        for page_idx in page:
            self.index_file.write(page_idx.write())

    def save_record_to_main_reorganise(self, value: record):
        self.reorganising_buffer.append(value)
        if len(self.reorganising_buffer) >= self.block_size*self.alpha:
            return self.reorganising_force_write_page

    def reorganising_force_write_page(self) -> page_index:
        self.reorganising_buffer += [record(0, '') for _ in range(self.block_size - len(self.reorganising_buffer))]
        self.save_page_to_main(self.reorganising_page_no, self.reorganising_buffer)
        p_idx = page_index(self.reorganising_buffer[0].index, self.reorganising_page_no)
        self.reorganising_buffer = []
        self.reorganising_page_no += 1
        return p_idx

    def create_enough_empty_pages(self):
        pages_needed = ceil((self.actual_invalid_records + self.actual_main_records)/(self.block_size*self.alpha))
        for _ in range(pages_needed):
            self.main_file.writelines(parse_page_to_str(self.create_page_of_records()))

    def erase_file(self, which: str):
        file_dir = {
            "index": self.index_file,
            "main": self.main_file,
            "overflow": self.overflow_file
        }
        if which in file_dir.keys():
            file_dir.get(which).truncate()

    def swap_mains(self):
        self.main_file, self.main_reorganise_file = self.main_reorganise_file, self.main_file

    def read_pages(self):
        pages = [page.rstrip('\n').split(' ') for page in self.index_file.readlines()]
        self.pages = [parse_pages(page) for page in pages]

    # TODO search page by bisect
    def find_page_by_key(self, key: int) -> int:
        i = 0
        while i < len(self.pages) and self.pages[i].index <= key:
            i += 1
        return self.pages[i - 1].page_no if i > 0 else -1

    def load_page(self, page_no: int, source) -> list:
        try:
            return [line for line in islice(source, page_no * self.block_size, (page_no + 1) * self.block_size)]
        except IndexError:
            return []

    def save_page_to_main(self, page_no: int, page_values: list):
        d = self.main_file.readlines()
        page_values = parse_page_to_str(page_values) + [record(0, '') for _ in
                                                        range(self.records_on_page - len(page_values))]
        d[page_no * self.records_on_page:(page_no + 1) * self.records_on_page] = page_values
        self.main_file.writelines(d)

    def load_page_from_overflow(self, pointer: int) -> list:
        which_page_of = self.find_out_page_from_overload(pointer)
        return self.load_page(which_page_of, self.overflow_file)

    def load_record_from_overflow(self, pointer: int) -> record:
        return parse_str_to_record(self.load_page_from_overflow(pointer)[pointer % self.block_size])

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
        d = self.overflow_file.readlines()
        page = [v_record.write() for v_record in page]
        d[page_no * self.block_size:(page_no + 1) * self.block_size] = page
        self.overflow_file.writelines(d)

    def save_record_to_overflow(self, value: record):
        d = self.overflow_file.readlines()
        d.append(value.write())
        self.overflow_file.writelines(d)
        return len(d) - 1

    def reload_file(self):
        self.main_file.flush()
