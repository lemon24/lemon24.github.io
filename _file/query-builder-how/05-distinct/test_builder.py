from textwrap import dedent

from builder import Query


def test_query_simple():
    query = (
        Query()
        .WITH(('alias', 'with'))
        .SELECT('select-one', ('alias', 'select-two'))
        .FROM('from-one', 'from-two')
        .JOIN('join')
        .WHERE('where-one', 'where-two')
        .SELECT_DISTINCT('select-three')
    )
    assert str(query) == dedent(
        """\
        WITH
            alias AS (
                with
            )
        SELECT DISTINCT
            select-one,
            select-two AS alias,
            select-three
        FROM
            from-one,
            from-two
        JOIN
            join
        WHERE
            where-one AND
            where-two
        """
    )
