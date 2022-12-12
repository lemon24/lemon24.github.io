import os
import sys
import time
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
    int_start = 0
    int_end = 16 ** len(prefix)
    int_prefix = int(prefix, 16)

    pos_start = 0
    pos_end = offset

    # magic_multiplier = 2  # buggy search_ends() infinite loop avoidance
    # times_smaller = (offset / 4096 * magic_multiplier) ** (1 / int(math.log(offset, 4096)))
    times_smaller = 8000  # for some reason, this is fastest

    while True:
        print(pos_end - pos_start)
        if pos_end - pos_start <= 4096:
            break

        pos_prefix = get_pos_prefix(int_prefix, int_start, int_end, pos_start, pos_end)
        file.seek(pos_prefix)

        skip_size = int((pos_end - pos_start) / times_smaller)
        int_start, int_end, pos_start, pos_end = search_ends(file, prefix, skip_size)

    file.seek(pos_start)


def get_pos_prefix(int_prefix, int_start, int_end, pos_start, pos_end):
    pos_normalized = (int_prefix - int_start) / (int_end - int_start)
    pos_prefix = int(pos_start + (pos_end - pos_start) * pos_normalized)
    return pos_prefix


def search_ends(file, prefix, offset):
    old_sign = sign = None
    start = end = None
    pos_start = pos_end = None

    while True:
        # FIXME: handle start or end of file
        file.readline()
        start = file.readline().partition(b':')[0]
        pos_start = file.tell()

        sign = 1 if start < prefix else -1

        if old_sign and sign != old_sign:
            break

        pos = file.seek(sign * offset, os.SEEK_CUR)

        end = start
        pos_end = pos_start
        old_sign = sign

    if end < start:
        start, end = end, start
        pos_start, pos_end = pos_end, pos_start

    int_start = int(start, 16)
    int_end = int(end, 16)

    return int_start, int_end, pos_start, pos_end


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
line = find_line(file, hexdigest.upper().encode(), size)
end = time.monotonic()

if line:
    times = int(line.decode().rstrip().partition(':')[2])
    print(f"pwned! seen {times:,} times before")
else:
    print("not found")

print(f"in {end-start:.6f} seconds")
