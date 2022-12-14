import sys

file = sys.stdin.buffer
outf = sys.stdout.buffer

while True:
    pos = file.tell()
    line = file.readline()
    if not line:
        break

    digest, _, _ = line.partition(b':')
    outf.write(bytes.fromhex(digest.decode())[:6])
    outf.write(pos.to_bytes(6, 'big'))

    file.seek((pos // 4096 + 1) * 4096)
    file.readline()
