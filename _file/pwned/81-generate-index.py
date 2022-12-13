import os, sys

file = sys.stdin.buffer
outf = sys.stdout.buffer

while True:
    pos = file.tell()
    line = file.readline()
    if not line:
        break

    outf.write(line.partition(b':')[0] + b':' + str(pos).encode() + b'\n')

    file.seek(2**12, os.SEEK_CUR)
    file.readline()
