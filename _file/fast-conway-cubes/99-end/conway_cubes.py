from itertools import product
from functools import lru_cache
from textwrap import dedent
import time


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


@lru_cache()
def make_directions(dimensions):
    ts = product((-1, 0, 1), repeat=dimensions)
    return [t for t in ts if t != (0,) * dimensions]


def make_get_active_neighbors_str(dimensions):
    ids = list(range(dimensions))
    return dedent(f"""

        def get_active_neighbors(world, active, coords):
            {', '.join(f'c{i}' for i in ids)} = coords

            if {' or '.join(f'c{i} < 1' for i in ids)}:
                if active:
                    raise RuntimeError(f"active on edge: {{coords}}")

            active_neighbors = 0
            for {', '.join(f'o{i}' for i in ids)} in {make_directions(dimensions)}:
                try:
                    active_neighbors += world[{']['.join(f'o{i} + c{i}' for i in ids)}]
                except IndexError:
                    if active:
                        raise RuntimeError(f"active on edge: {{coords}}")

            return active_neighbors

    """)

@lru_cache()
def make_get_active_neighbors(dimensions):
    context = {}
    exec(make_get_active_neighbors_str(dimensions), context)
    return context['get_active_neighbors']


def guess_dimensions(world):
    dimensions = 0
    while isinstance(world, list):
        dimensions += 1
        world = world[0]
    return dimensions

def ndenumerate(world, dimensions=None):
    dimensions = dimensions or guess_dimensions(world)

    if dimensions == 1:
        for i, value in enumerate(world):
            yield (i,), value
        return

    for i, part in enumerate(world):
        for t, value in ndenumerate(part, dimensions - 1):
            yield (i,) + t, value


def simulate(old, new):
    dimensions = guess_dimensions(old)
    get_active_neighbors = make_get_active_neighbors(dimensions)

    for coords, active in ndenumerate(old, dimensions):
        active_neighbors = get_active_neighbors(old, active, coords)

        if active:
            new_active = int(2 <= active_neighbors <= 3)
        else:
            new_active = int(active_neighbors == 3)

        target = new
        for coord in coords[:-1]:
            target = target[coord]
        target[coords[-1]] = new_active


def make_world(shape):
    head, *rest = shape
    if not rest:
        return [0] * head
    return [make_world(rest) for _ in range(head)]


def copy_centered_2d(src, dst):
    y_offset = (len(dst) - len(src)) // 2
    x_offset = (len(dst[0]) - len(src[0])) // 2
    for y, line in enumerate(src):
        for x, point in enumerate(line):
            dst[y + y_offset][x + x_offset] = point


def simulate_forever(shape, input):
    old = make_world(shape)
    new = make_world(shape)

    copy_dst = old
    for n in shape[:-2]:
        copy_dst = copy_dst[(n - 1) // 2]
    copy_centered_2d(input, copy_dst)

    yield old
    while True:
        simulate(old, new)
        old, new = new, old
        yield old


def run(size, dimensions, input, format_world=None, cycles=6):
    worlds = simulate_forever((size,) * dimensions, input)

    total_time = 0
    start = time.perf_counter()
    for cycle, world in zip(range(cycles + 1), worlds):
        end = time.perf_counter()

        print(f"after cycle #{cycle} ({end - start :.2f}s): ", end='')
        if format_world:
            print()
            print(format_world(world))
        else:
            print('...')

        total_time += end - start
        start = time.perf_counter()

    active_cubes = sum(active for _, active in ndenumerate(world))
    print(f"the result is {active_cubes} ({total_time:.2f}s)")
    print()

    return world, active_cubes


TEST_INPUT = """\
.#.
..#
###
"""

INPUT = """\
.##...#.
.#.###..
..##.#.#
##...#.#
#..#...#
#..###..
.##.####
..#####.
"""

def main(args):
    input = {'test': TEST_INPUT, 'real': INPUT}[args[0]]
    size, dimensions, cycles = map(int, args[1:4])
    run(
        size,
        dimensions,
        parse_input(input),
        format_world=format_2d if dimensions == 2 else None,
        cycles=cycles,
    )

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
