INDEX_LENGTH = 5
MAX_RECORD_LENGTH = 30
MAX_PAGE_LENGTH = 3
POINTER_LENGTH = 8

test = 'write lines\n' * 10000
with open('/home/kuba/test_log.txt', 'w') as f:
    f.write(test)