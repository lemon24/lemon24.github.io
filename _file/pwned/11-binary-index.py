import os
import sys
import time
import bisect
import getpass
import hashlib


def find_line(file, prefix, index):
    skip_to_before_line_index(file, prefix, index)
    return find_line_linear(file, prefix)


def find_line_linear(lines, prefix):
    for line in lines:
        if line.startswith(prefix):
            return line
        if line > prefix:
            break
    return None


def skip_to_before_line_index(file, prefix, index):
    item_prefix = bytes.fromhex(prefix.decode())[:6]
    item = find_lt(index, item_prefix)
    offset = int.from_bytes(item[6:], 'big') if item else 0
    file.seek(offset)


def find_lt(a, x):
    i = bisect.bisect_left(a, x)
    if i:
        return a[i-1]
    return None


class BytesArray:

    item_size = 12

    def __init__(self, file):
        self.file = file

    def __getitem__(self, index):
        self.file.seek(index * self.item_size)
        buffer = self.file.read(self.item_size)
        if len(buffer) != self.item_size:
            raise IndexError(index)  # out of bounds
        return buffer

    def __len__(self):
        self.file.seek(0, os.SEEK_END)
        size = self.file.tell()
        return size // self.item_size


path = sys.argv[1]
file = open(path, 'rb')

index_path = sys.argv[2]
index = BytesArray(open(index_path, 'rb'))

try:
    password = sys.argv[3]
except IndexError:
    password = getpass.getpass()
hexdigest = hashlib.sha1(password.encode()).hexdigest()
del password

print("looking for", hexdigest)

start = time.monotonic()
line = find_line(file, hexdigest.upper().encode(), index)
end = time.monotonic()

if line:
    times = int(line.decode().rstrip().partition(':')[2])
    print(f"pwned! seen {times:,} times before")
else:
    print("not found")

print(f"in {end-start:.6f} seconds")
