import wrapt
from yaml import SafeDumper, SafeLoader


class Loader(SafeLoader):
    pass


class Dumper(SafeDumper):
    pass


class Hashable(wrapt.ObjectProxy):
    def __hash__(self):
        return object.__hash__(self)

    def __eq__(self, other):
        return object.__eq__(self, other)

    def __repr__(self):
        return f"{type(self).__name__}({self.__wrapped__!r})"


def construct_any_key_mapping(self, data):
    rv = {}
    for key, value in self.construct_pairs(data):
        try:
            rv[key] = value
        except TypeError:
            rv[Hashable(key)] = value
    return rv

Loader.add_constructor('tag:yaml.org,2002:map', construct_any_key_mapping)


def represent_any_key_dict(self, data):
    pairs = []
    for key, value in data.items():
        if isinstance(key, Hashable):
            key = key.__wrapped__
        pairs.append((key, value))
    rv = self.represent_dict(pairs)
    return rv

Dumper.add_representer(dict, represent_any_key_dict)


import pytest
import yaml

TEXT = """\
[0,0]: one
{0: 1}: {[]: three}
"""


def test_load():
    data = yaml.load(TEXT, Loader=Loader)
    assert repr(data) == (
        "{"
            "Hashable([0, 0]): 'one', "
            "Hashable({0: 1}): {Hashable([]): 'three'}"
        "}"
    )


def test_roundtrip():
    data = yaml.load(TEXT, Loader=Loader)
    assert repr(data) == repr(yaml.load(yaml.dump(data, Dumper=Dumper), Loader=Loader))
