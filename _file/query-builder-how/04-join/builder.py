import functools
import textwrap
from collections import defaultdict
from typing import NamedTuple


class Query:

    keywords = [
        'WITH',
        'SELECT',
        'FROM',
        'WHERE',
        'GROUP BY',
        'HAVING',
        'ORDER BY',
        'LIMIT',
    ]

    separators = dict(WHERE='AND', HAVING='AND')
    default_separator = ','

    formats = (
        defaultdict(lambda: '{value}'),
        defaultdict(lambda: '{value} AS {alias}', WITH='{alias} AS {value}'),
    )

    subquery_keywords = {'WITH'}
    fake_keywords = dict(JOIN='FROM')

    def __init__(self):
        self.data = {k: [] for k in self.keywords}

    def add(self, keyword, *args):
        keyword, fake_keyword = self._resolve_fakes(keyword)
        target = self.data[keyword]

        kwargs = {}
        if fake_keyword:
            kwargs.update(keyword=fake_keyword)
        if keyword in self.subquery_keywords:
            kwargs.update(is_subquery=True)

        for arg in args:
            target.append(_Thing.from_arg(arg, **kwargs))

        return self

    def _resolve_fakes(self, keyword):
        for part, real in self.fake_keywords.items():
            if part in keyword:
                return real, keyword
        return keyword, ''

    def __getattr__(self, name):
        if not name.isupper():
            return getattr(super(), name)
        return functools.partial(self.add, name.replace('_', ' '))

    def __str__(self):
        return ''.join(self._lines())

    def _lines(self):
        for keyword, things in self.data.items():
            if not things:
                continue

            yield f'{keyword}\n'

            grouped = [], []
            for thing in things:
                grouped[bool(thing.keyword)].append(thing)
            for group in grouped:
                yield from self._lines_keyword(keyword, group)

    def _lines_keyword(self, keyword, things):
        for i, thing in enumerate(things, 1):
            last = i == len(things)

            if thing.keyword:
                yield thing.keyword + '\n'

            format = self.formats[bool(thing.alias)][keyword]
            value = thing.value
            if thing.is_subquery:
                value = f'(\n{self._indent(value)}\n)'
            yield self._indent(format.format(value=value, alias=thing.alias))

            if not last and not thing.keyword:
                try:
                    yield ' ' + self.separators[keyword]
                except KeyError:
                    yield self.default_separator

            yield '\n'

    _indent = functools.partial(textwrap.indent, prefix='    ')


class _Thing(NamedTuple):
    value: str
    alias: str = ''
    keyword: str = ''
    is_subquery: bool = False

    @classmethod
    def from_arg(cls, arg, **kwargs):
        if isinstance(arg, str):
            alias, value = '', arg
        elif len(arg) == 2:
            alias, value = arg
        else:
            raise ValueError(f"invalid arg: {arg!r}")
        return cls(_clean_up(value), _clean_up(alias), **kwargs)


def _clean_up(thing: str) -> str:
    return textwrap.dedent(thing.rstrip()).strip()
