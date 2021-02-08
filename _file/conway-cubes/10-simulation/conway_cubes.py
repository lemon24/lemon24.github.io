CHARACTERS = '.#'
CHR_TO_NUM = {c: i for i, c in enumerate(CHARACTERS)}

def parse_input(input):
    return [
        [CHR_TO_NUM[c] for c in line]
        for line in input.splitlines()
    ]

NUM_TO_CHR = dict(enumerate(CHARACTERS))

def format_2d(plane):
    return ''.join(
        ''.join(NUM_TO_CHR[n] for n in line) + '\n'
        for line in plane
    )

TEST_INPUT = """\
.#.
..#
###
"""

assert format_2d(parse_input(TEST_INPUT)) == TEST_INPUT


def simulate(old, new):
    for y, line in enumerate(old):
        for x, active in enumerate(line):

            active_neighbors = 0
            for i in -1, 0, 1:
                for j in -1, 0, 1:

                    if i == j == 0:
                        continue

                    nx = x + i
                    ny = y + j

                    if nx < 0 or ny < 0:
                        if active:
                            raise RuntimeError(f"active on edge: {(x, y)}")
                        continue

                    try:
                        active_neighbors += old[ny][nx]
                    except IndexError:
                        if active:
                            raise RuntimeError(f"active on edge: {(x, y)}")
                        continue

            if active:
                new_active = int(2 <= active_neighbors <= 3)
            else:
                new_active = int(active_neighbors == 3)

            new[y][x] = new_active


x_size = y_size = 8

world = [[0] * x_size for _ in range(y_size)]


input = parse_input(TEST_INPUT)
x_offset = (x_size - len(input[0])) // 2
y_offset = (y_size - len(input)) // 2

for y, line in enumerate(input):
    for x, active in enumerate(line):
        world[y + y_offset][x + x_offset] = active

print(format_2d(world))


old = world
new = [[0] * x_size for _ in range(y_size)]

for cycle in range(6):
    simulate(old, new)
    new, old = old, new
    print(f"after cycle #{cycle + 1}")
    print(format_2d(old))


world = old

active_cubes = sum(active for line in world for active in line)
print("the result is", active_cubes)

assert active_cubes == 5
assert world == parse_input("""\
........
........
........
........
.....#..
...#.#..
....##..
........
""")
