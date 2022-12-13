import os
import sys
import time
import bisect
import getpass
import hashlib


class ItemArray:

    item_size = 24

    def __init__(self, file, size):
        self.file = file
        self.size = size

    def __getitem__(self, index):
        offset = index * self.item_size
        if self.file.seek(offset) != offset:
            raise IndexError(index)
        buffer = self.file.read(self.item_size)
        if len(buffer) != self.item_size:
            raise IndexError(index)
        return buffer

    def __len__(self):
        return self.size // self.item_size


def find_line(file, hexdigest, size):
    digest = bytes.fromhex(hexdigest)
    array = ItemArray(file, size)
    line = array[bisect.bisect(array, digest)]
    if line.startswith(digest):
        return line
    return None


path = sys.argv[1]
file = open(path, 'rb')
size = os.stat(path).st_size

try:
    password = sys.argv[2]
except IndexError:
    password = getpass.getpass()
hexdigest = hashlib.sha1(password.encode()).hexdigest()
del password

print("looking for", hexdigest)

start = time.monotonic()
line = find_line(file, hexdigest, size)
end = time.monotonic()

if line:
    times = int.from_bytes(line[20:], 'big')
    print(f"pwned! seen {times:,} times before")
else:
    print("not found")

print(f"in {end-start:.6f} seconds")
