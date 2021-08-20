from textwrap import dedent

from builder import Query


def test_query_simple():
    query = (
        Query()
        .SELECT('select')
        .FROM('from-one', 'from-two')
        .WHERE('where-one', 'where-two')
    )
    assert str(query) == dedent(
        """\
        SELECT
            select
        FROM
            from-one,
            from-two
        WHERE
            where-one AND
            where-two
        """
    )
