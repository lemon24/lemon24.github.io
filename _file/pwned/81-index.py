import os
import sys
import time
import bisect
import getpass
import hashlib


def find_line(file, prefix, size):
    skip_to_before_line(file, prefix, size)
    return find_line_linear(file, prefix)


def find_line_linear(lines, prefix):
    for line in lines:
        if line.startswith(prefix):
            return line
        if line > prefix:
            break
    return None


def skip_to_before_line(file, prefix, offset):
    while offset > 2**8:
        offset //= 2
        skip_to_before_line_linear(file, prefix, offset)


def skip_to_before_line_linear(file, prefix, offset):
    old_position = file.tell()

    while True:
        file.seek(offset, os.SEEK_CUR)

        file.readline()
        line = file.readline()
        # print("jumped to", (line or b'<eof>').decode().rstrip())

        if not line or line > prefix:
            file.seek(old_position)
            break

        old_position = file.tell()


path = sys.argv[1]
file = open(path, 'rb')
size = os.stat(path).st_size

try:
    password = sys.argv[2]
except IndexError:
    password = getpass.getpass()
hexdigest = hashlib.sha1(password.encode()).hexdigest()
del password
hexdigest_bytes = hexdigest.upper().encode()

index_file = open('index.txt', 'rb')
index_size = os.stat('index.txt').st_size

print("looking for", hexdigest)

start = time.monotonic()

line = find_line(index_file, hexdigest_bytes, index_size)
if not line:
    line = index_file.readline()
    index_file.seek(-(len(line) * 3 + 10), os.SEEK_CUR)
    index_file.readline()
    line = index_file.readline()

if line:
    file.seek(int(line.partition(b':')[2]))
    file.readline()

line = find_line(file, hexdigest_bytes, 2**12)

end = time.monotonic()

if line:
    times = int(line.decode().rstrip().partition(':')[2])
    print(f"pwned! seen {times:,} times before")
else:
    print("not found")

print(f"in {end-start:.6f} seconds")
