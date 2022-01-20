import wrapt
import yaml


class Loader(yaml.SafeLoader):
    pass

class Dumper(yaml.SafeDumper):
    pass


class Tagged(wrapt.ObjectProxy):

    # tell wrapt to set the attribute on the proxy, not the wrapped object
    tag = None

    def __init__(self, tag, wrapped):
        super().__init__(wrapped)
        self.tag = tag

    def __repr__(self):
        return f"{type(self).__name__}({self.tag!r}, {self.__wrapped__!r})"


def construct_undefined(self, node):
    if isinstance(node, yaml.nodes.ScalarNode):
        value = self.construct_scalar(node)
    elif isinstance(node, yaml.nodes.SequenceNode):
        value = self.construct_sequence(node)
    elif isinstance(node, yaml.nodes.MappingNode):
        value = self.construct_mapping(node)
    else:
        assert False, f"unexpected node: {node!r}"
    return Tagged(node.tag, value)

Loader.add_constructor(None, construct_undefined)


def represent_tagged(self, data):
    assert isinstance(data, Tagged), data
    node = self.represent_data(data.__wrapped__)
    node.tag = data.tag
    return node

Dumper.add_representer(Tagged, represent_tagged)


class Pairs(list):
    def __repr__(self):
        return f"{type(self).__name__}({super().__repr__()})"


def construct_mapping(self, node):
    value = self.construct_pairs(node)
    try:
        return dict(value)
    except TypeError:
        return Pairs(value)

Loader.construct_mapping = construct_mapping
Loader.add_constructor('tag:yaml.org,2002:map', Loader.construct_mapping)


def represent_pairs(self, data):
    assert isinstance(data, Pairs), data
    node = self.represent_dict(data)
    return node

Dumper.add_representer(Pairs, represent_pairs)
