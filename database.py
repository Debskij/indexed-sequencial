from itertools import islice

from record import *


def parse_pages(page_str: list) -> page_index:
    return page_index(int(page_str[0]), int(page_str[1]))


def parse_page_to_str(pages: list) -> list:
    return [page.write() for page in pages]


def parse_str_to_record(record_str: str) -> record:
    r = [x.strip() for x in record_str.split(' ')]
    return record(int(r[0]), r[1])


def create_new_file(name: str):
    f = open(name, 'w')
    f.close()
    return open(name, 'r+')


def create_reorganising_file(path: str):
    file_handle = create_new_file(path)
    return file_handle


class database:
    def __init__(self, page_file_path: str, main_file_path: str, overflow_area_path: str,
                 block_size: int, page_utilization_factor: float, limit_of_overflow: float,
                 records_on_page: int):
        self.index_file = open(page_file_path, 'r+')
        self.main_file = open(main_file_path, 'r+')
        self.overflow_file = open(overflow_area_path, 'r+')
        self.block_size = block_size
        self.alpha = page_utilization_factor
        self.limit_of_overflow = limit_of_overflow
        self.records_on_page = records_on_page
        self.actual_overflow_page = 0
        self.read_pages()

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
        return [line for line in islice(source, page_no * self.block_size, (page_no + 1) * self.block_size)]

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
        return self.load_page(page_no, self.main_file)

    def find_out_page_from_overload(self, pointer: int) -> int:
        return pointer // self.block_size

    def update_record_in_overflow(self, value: record, pointer: int):
        page_of = self.load_page_from_overflow(pointer)
        page_of[pointer % self.block_size] = value.write()
        self.update_page_in_overflow(self.find_out_page_from_overload(pointer), page_of)

    def update_page_in_overflow(self, page_no: int, page: list):
        d = self.overflow_file.readlines()
        d[page_no*self.block_size:(page_no+1)*self.block_size] = page
        self.overflow_file.writelines(d)

    def save_record_to_overflow(self, value: record):
        d = self.overflow_file.readlines()
        d.append(value.write())
        self.overflow_file.writelines(d)
        return len(d) - 1

    def reload_file(self):
        self.main_file.flush()
