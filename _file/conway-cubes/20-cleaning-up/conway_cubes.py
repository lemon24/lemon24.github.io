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


def get_active_neighbors(world, active, x, y):
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
                active_neighbors += world[ny][nx]
            except IndexError:
                if active:
                    raise RuntimeError(f"active on edge: {(x, y)}")
                continue

    return active_neighbors


def simulate(old, new):
    for y, line in enumerate(old):
        for x, active in enumerate(line):
            active_neighbors = get_active_neighbors(old, active, x, y)

            if active:
                new_active = int(2 <= active_neighbors <= 3)
            else:
                new_active = int(active_neighbors == 3)

            new[y][x] = new_active


def make_world(x, y):
    return [[0] * x for _ in range(y)]


def copy_centered_2d(src, dst):
    y_offset = (len(dst) - len(src)) // 2
    x_offset = (len(dst[0]) - len(src[0])) // 2
    for y, line in enumerate(src):
        for x, point in enumerate(line):
            dst[y + y_offset][x + x_offset] = point


def simulate_forever(size, input):
    old = make_world(size, size)
    new = make_world(size, size)

    copy_centered_2d(input, old)

    yield old
    while True:
        simulate(old, new)
        old, new = new, old
        yield old


def run(size, input, format_world=None):
    worlds = simulate_forever(size, input)

    for cycle, world in zip(range(6 + 1), worlds):
        print(f"after cycle #{cycle}: ", end='')
        if format_world:
            print()
            print(format_world(world))
        else:
            print('...')

    active_cubes = sum(active for line in world for active in line)
    print("the result is", active_cubes)
    print()

    return world, active_cubes


world, active_cubes = run(8, parse_input(TEST_INPUT), format_world=format_2d)

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
