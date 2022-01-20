import pytest
import yaml

from any_yaml import Loader, Dumper, Tagged, Pairs


BASIC_TEXT = """\
one: !myscalar string
two: !mymapping
  three: !mysequence [1, 2]
"""

BASIC_DATA = {
    'one': Tagged('!myscalar', 'string'),
    'two': Tagged('!mymapping', {'three': Tagged('!mysequence', [1, 2])}),
}

UNHASHABLE_TEXT = """\
[0,0]: one
!key {0: 1}: {[]: !value three}
"""

UNHASHABLE_DATA = Pairs(
    [
        ([0, 0], 'one'),
        (Tagged('!key', {0: 1}), Pairs([([], Tagged('!value', 'three'))])),
    ]
)

DATA = [
    (BASIC_TEXT, BASIC_DATA),
    (UNHASHABLE_TEXT, UNHASHABLE_DATA),
]


@pytest.mark.parametrize('text, data', DATA)
def test_load(text, data):
    assert yaml.load(text, Loader=Loader) == data


@pytest.mark.parametrize('text', [t[0] for t in DATA])
def test_roundtrip(text):
    data = yaml.load(text, Loader=Loader)
    assert data == yaml.load(yaml.dump(data, Dumper=Dumper), Loader=Loader)


def test_dump_error():
    with pytest.raises(yaml.representer.RepresenterError):
        yaml.dump(object(), Dumper=Dumper)
