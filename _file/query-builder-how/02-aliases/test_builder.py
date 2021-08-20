from textwrap import dedent

from builder import Query


def test_query_simple():
    query = (
        Query()
        .SELECT('select-one', ('alias', 'select-two'))
        .FROM('from-one', 'from-two')
        .WHERE('where-one', 'where-two')
    )
    assert str(query) == dedent(
        """\
        SELECT
            select-one,
            select-two AS alias
        FROM
            from-one,
            from-two
        WHERE
            where-one AND
            where-two
        """
    )
