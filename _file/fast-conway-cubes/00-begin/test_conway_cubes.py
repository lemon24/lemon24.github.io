from textwrap import dedent

import pytest

from conway_cubes import TEST_INPUT, format_2d, parse_input, run


def test_parse_roundtrip():
    assert format_2d(parse_input(TEST_INPUT)) == TEST_INPUT

def test_2():
    world, active_cubes = run(8, 2, parse_input(TEST_INPUT), format_world=format_2d)
    assert active_cubes == 5
    assert world == parse_input(dedent("""\
        ........
        ........
        ........
        ........
        .....#..
        ...#.#..
        ....##..
        ........
    """))

def test_3():
    _, active_cubes = run(16, 3, parse_input(TEST_INPUT))
    assert active_cubes == 112

def test_4():
    _, active_cubes = run(16, 4, parse_input(TEST_INPUT))
    assert active_cubes == 848


@pytest.mark.parametrize('input',
    [
        """\
        #..
        ...
        ...
        """,
        """\
        .#.
        ...
        ...
        """,
        """\
        ...
        ..#
        ...
        """,
        """\
        ...
        ...
        .#.
        """,
    ]
)
@pytest.mark.parametrize('dimensions', [2, 3, 4])
def test_edge_errors(input, dimensions):
    with pytest.raises(RuntimeError):
        run(3, dimensions, parse_input(dedent(input)), cycles=1)


@pytest.mark.parametrize('input, expected_output',
    [
        (
            """\
            .....
            .#...
            .#...
            .#...
            .....
            """,
            """\
            .....
            .....
            ###..
            .....
            .....
            """
        ),
        (
            """\
            .....
            .....
            .....
            .###.
            .....
            """,
            """\
            .....
            .....
            ..#..
            ..#..
            ..#..
            """
        ),

    ]
)
def test_edge_ok(input, expected_output):
    world, _ = run(5, 2, parse_input(dedent(input)), cycles=1)
    assert format_2d(world) == dedent(expected_output)
