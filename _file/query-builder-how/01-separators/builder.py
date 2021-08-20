import functools
import textwrap


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

    def __init__(self):
        self.data = {k: [] for k in self.keywords}

    def add(self, keyword, *args):
        target = self.data[keyword]

        for arg in args:
            target.append(_clean_up(arg))

        return self

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
            yield from self._lines_keyword(keyword, things)

    def _lines_keyword(self, keyword, things):
        for i, thing in enumerate(things, 1):
            last = i == len(things)

            yield self._indent(thing)

            if not last:
                try:
                    yield ' ' + self.separators[keyword]
                except KeyError:
                    yield self.default_separator

            yield '\n'

    _indent = functools.partial(textwrap.indent, prefix='    ')


def _clean_up(thing: str) -> str:
    return textwrap.dedent(thing.rstrip()).strip()
