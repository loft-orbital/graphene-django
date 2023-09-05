import pytest
from graphql_relay import (
    Connection,
    Edge,
    PageInfo,
    offset_to_cursor,
)

from ..connection import connection_from_sized_sliceable

array_abcde = ["A", "B", "C", "D", "E"]

cursor_a = "YXJyYXljb25uZWN0aW9uOjA="
cursor_b = "YXJyYXljb25uZWN0aW9uOjE="
cursor_c = "YXJyYXljb25uZWN0aW9uOjI="
cursor_d = "YXJyYXljb25uZWN0aW9uOjM="
cursor_e = "YXJyYXljb25uZWN0aW9uOjQ="

edge_a = Edge(node="A", cursor=cursor_a)
edge_b = Edge(node="B", cursor=cursor_b)
edge_c = Edge(node="C", cursor=cursor_c)
edge_d = Edge(node="D", cursor=cursor_d)
edge_e = Edge(node="E", cursor=cursor_e)


class TestArgs:
    def test_forbids_first_and_last(self):
        with pytest.raises(ValueError) as exc_info:
            connection_from_sized_sliceable(
                array_abcde,
                {"first": 1, "last": 1},
            )
        assert str(exc_info.value) == "Mixing 'first' and 'last' is not supported."

    def test_forbids_before_and_after(self):
        with pytest.raises(ValueError) as exc_info:
            connection_from_sized_sliceable(
                array_abcde,
                {"before": cursor_c, "after": cursor_a},
            )
        assert str(exc_info.value) == "Mixing 'before' and 'after' is not supported."

    def test_forbids_first_and_before(self):
        with pytest.raises(ValueError) as exc_info:
            connection_from_sized_sliceable(
                array_abcde,
                {"first": 1, "before": cursor_b},
            )
        assert str(exc_info.value) == "Mixing 'first' and 'before' is not supported."

    def test_forbids_last_and_after(self):
        with pytest.raises(ValueError) as exc_info:
            connection_from_sized_sliceable(
                array_abcde,
                {"last": 1, "after": cursor_a},
            )
        assert str(exc_info.value) == "Mixing 'last' and 'after' is not supported."


class TestBasicSlicing:
    def test_returns_all_elements_without_filters(self):
        c = connection_from_sized_sliceable(array_abcde, {})
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )

    def test_respects_a_smaller_first(self):
        c = connection_from_sized_sliceable(array_abcde, {"first": 2})
        assert c == Connection(
            edges=[
                edge_a,
                edge_b,
            ],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_b,
                hasPreviousPage=False,
                hasNextPage=True,
            ),
        )

    def test_respects_an_overly_large_first(self):
        c = connection_from_sized_sliceable(array_abcde, {"first": 10})
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )

    def test_respects_a_smaller_last(self):
        c = connection_from_sized_sliceable(array_abcde, {"last": 2})
        assert c == Connection(
            edges=[edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_d,
                endCursor=cursor_e,
                hasPreviousPage=True,
                hasNextPage=False,
            ),
        )

    def test_respects_an_overly_large_last(self):
        c = connection_from_sized_sliceable(array_abcde, {"last": 10})
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )


class TestPagination:
    def test_respects_first(self):
        c = connection_from_sized_sliceable(
            array_abcde,
            {"first": 2},
        )
        assert c == Connection(
            edges=[edge_a, edge_b],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_b,
                hasPreviousPage=False,
                hasNextPage=True,
            ),
        )

        c = connection_from_sized_sliceable(
            array_abcde,
            {"first": 0},
        )
        assert c == Connection(
            edges=[],
            pageInfo=PageInfo(
                startCursor=None,
                endCursor=None,
                hasPreviousPage=False,
                hasNextPage=True,
            ),
        )

        c = connection_from_sized_sliceable(
            array_abcde,
            {"first": 5},
        )
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )

        c = connection_from_sized_sliceable(
            array_abcde,
            {"first": 100},
        )
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )

    def test_respects_last(self):
        c = connection_from_sized_sliceable(
            array_abcde,
            {"last": 2},
        )
        assert c == Connection(
            edges=[edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_d,
                endCursor=cursor_e,
                hasPreviousPage=True,
                hasNextPage=False,
            ),
        )

        c = connection_from_sized_sliceable(
            array_abcde,
            {"last": 0},
        )
        assert c == Connection(
            edges=[],
            pageInfo=PageInfo(
                startCursor=None,
                endCursor=None,
                hasPreviousPage=True,
                hasNextPage=False,
            ),
        )

        c = connection_from_sized_sliceable(
            array_abcde,
            {"last": 5},
        )
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )

        c = connection_from_sized_sliceable(
            array_abcde,
            {"last": 100},
        )
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )

    def test_respects_after(self):
        c = connection_from_sized_sliceable(
            array_abcde,
            {"after": cursor_b},
        )
        assert c == Connection(
            edges=[edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_c,
                endCursor=cursor_e,
                hasPreviousPage=True,
                hasNextPage=False,
            ),
        )

        c = connection_from_sized_sliceable(
            array_abcde,
            {"after": cursor_e},
        )
        assert c == Connection(
            edges=[],
            pageInfo=PageInfo(
                startCursor=None,
                endCursor=None,
                hasPreviousPage=True,
                hasNextPage=False,
            ),
        )

    def test_respects_before(self):
        c = connection_from_sized_sliceable(
            array_abcde,
            {"before": cursor_c},
        )
        assert c == Connection(
            edges=[edge_a, edge_b],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_b,
                hasPreviousPage=False,
                hasNextPage=True,
            ),
        )

        c = connection_from_sized_sliceable(
            array_abcde,
            {"before": cursor_a},
        )
        assert c == Connection(
            edges=[],
            pageInfo=PageInfo(
                startCursor=None,
                endCursor=None,
                hasPreviousPage=False,
                hasNextPage=True,
            ),
        )

    def test_respects_first_and_after(self):
        c = connection_from_sized_sliceable(
            array_abcde, {"first": 2, "after": cursor_b}
        )
        assert c == Connection(
            edges=[edge_c, edge_d],
            pageInfo=PageInfo(
                startCursor=cursor_c,
                endCursor=cursor_d,
                hasPreviousPage=True,
                hasNextPage=True,
            ),
        )

    def test_respects_first_and_after_with_long_first(self):
        c = connection_from_sized_sliceable(
            array_abcde, {"first": 10, "after": cursor_b}
        )
        assert c == Connection(
            edges=[edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_c,
                endCursor=cursor_e,
                hasPreviousPage=True,
                hasNextPage=False,
            ),
        )

    def test_respects_last_and_before(self):
        c = connection_from_sized_sliceable(
            array_abcde, {"last": 2, "before": cursor_d}
        )
        assert c == Connection(
            edges=[edge_b, edge_c],
            pageInfo=PageInfo(
                startCursor=cursor_b,
                endCursor=cursor_c,
                hasPreviousPage=True,
                hasNextPage=True,
            ),
        )

    def test_respects_last_and_before_with_long_last(self):
        c = connection_from_sized_sliceable(
            array_abcde, {"last": 10, "before": cursor_d}
        )
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_c,
                hasPreviousPage=False,
                hasNextPage=True,
            ),
        )


class TestCursorEdgeCases:
    def test_throws_an_error_if_first_smaller_than_zero(self):
        with pytest.raises(ValueError) as exc_info:
            connection_from_sized_sliceable(array_abcde, {"first": -1})
        assert str(exc_info.value) == (
            "Argument 'first' must be a non-negative integer."
        )

    def test_throws_an_error_if_last_smaller_than_zero(self):
        with pytest.raises(ValueError) as exc_info:
            connection_from_sized_sliceable(array_abcde, {"last": -1})
        assert str(exc_info.value) == (
            "Argument 'last' must be a non-negative integer."
        )

    def test_returns_all_elements_if_cursors_are_invalid(self):
        c1 = connection_from_sized_sliceable(array_abcde, {"before": "InvalidBase64"})

        c2 = connection_from_sized_sliceable(array_abcde, {"after": "InvalidBase64"})

        invalid_unicode_in_base64 = "9JCAgA=="  # U+110000

        c3 = connection_from_sized_sliceable(
            array_abcde,
            {"before": invalid_unicode_in_base64},
        )

        c4 = connection_from_sized_sliceable(
            array_abcde,
            {"after": invalid_unicode_in_base64},
        )

        assert c1 == c2 == c3 == c4
        assert c1 == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )

    def test_cursors_are_on_the_outside(self):
        c = connection_from_sized_sliceable(
            array_abcde, {"before": offset_to_cursor(6)}
        )
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )

        # `hasNextPage=True` because the spec says:
        # "If before is set: If the server can efficiently determine that elements exist following `before`, return true."
        # and `before` is before the beginning of the array so there are elements after.
        c = connection_from_sized_sliceable(
            array_abcde, {"before": offset_to_cursor(-1)}
        )
        assert c == Connection(
            edges=[],
            pageInfo=PageInfo(
                startCursor=None,
                endCursor=None,
                hasPreviousPage=False,
                hasNextPage=True,
            ),
        )

        # `hasPreviousPage=True` because the spec says:
        # "If after is set: If the server can efficiently determine that elements exist prior to `after`, return true"
        # and `after` is after the end of the array so there are elements before.
        c = connection_from_sized_sliceable(array_abcde, {"after": offset_to_cursor(6)})
        assert c == Connection(
            edges=[],
            pageInfo=PageInfo(
                startCursor=None,
                endCursor=None,
                hasPreviousPage=True,
                hasNextPage=False,
            ),
        )

        c = connection_from_sized_sliceable(
            array_abcde, {"after": offset_to_cursor(-1)}
        )
        assert c == Connection(
            edges=[edge_a, edge_b, edge_c, edge_d, edge_e],
            pageInfo=PageInfo(
                startCursor=cursor_a,
                endCursor=cursor_e,
                hasPreviousPage=False,
                hasNextPage=False,
            ),
        )
