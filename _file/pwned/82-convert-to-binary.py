import sys

file = open(sys.argv[1], 'rb', buffering=64 * 2**20)
outf = open(sys.argv[2], 'wb', buffering=16 * 2**20)

for line in file:
    digest, _, count = line.partition(b':')
    outf.write(bytes.fromhex(digest.decode()))
    outf.write(int(count).to_bytes(4, 'big'))
