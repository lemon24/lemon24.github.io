import os
import sys
import time
import getpass
import hashlib


def find_line(file, prefix):
    skip_to_before_line(file, prefix, 16 * 2**20)
    return find_line_linear(file, prefix)


def find_line_linear(lines, prefix):
    for line in lines:
        if line.startswith(prefix):
            return line
        if line > prefix:
            break
    return None


def skip_to_before_line(file, prefix, offset):
    old_position = file.tell()

    while True:
        file.seek(offset, os.SEEK_CUR)

        file.readline()
        line = file.readline()
        # print("jumped to", (line or b'<eof>').decode().rstrip())

        if not line or line >= prefix:
            file.seek(old_position)
            break

        old_position = file.tell()


path = sys.argv[1]
file = open(path, 'rb')

try:
    password = sys.argv[2]
except IndexError:
    password = getpass.getpass()
hexdigest = hashlib.sha1(password.encode()).hexdigest()
del password

print("looking for", hexdigest)

start = time.monotonic()
line = find_line(file, hexdigest.upper().encode())
end = time.monotonic()

if line:
    times = int(line.decode().rstrip().partition(':')[2])
    print(f"pwned! seen {times:,} times before")
else:
    print("not found")

print(f"in {end-start:.6f} seconds")
