import pytest

from ...compat import ArrayField, MissingType


@pytest.mark.skipif(ArrayField is MissingType, reason="ArrayField should exist")
def test_array_field_contains_multiple(use_dataloaders, schema):
    """
    Test contains filter on a array field of string.
    """

    if use_dataloaders:
        # this test uses a QuerySet mock FakeQuerySet that does not support dataloaders
        return

    query = """
    query {
        events (tags_Contains: ["concert", "music"]) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    result = schema.execute(query, execution_context_class=use_dataloaders)
    assert not result.errors
    assert result.data["events"]["edges"] == [
        {"node": {"name": "Live Show"}},
    ]


@pytest.mark.skipif(ArrayField is MissingType, reason="ArrayField should exist")
def test_array_field_contains_one(schema):
    """
    Test contains filter on a array field of string.
    """

    query = """
    query {
        events (tags_Contains: ["music"]) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    result = schema.execute(query)
    assert not result.errors
    assert result.data["events"]["edges"] == [
        {"node": {"name": "Live Show"}},
        {"node": {"name": "Musical"}},
    ]


@pytest.mark.skipif(ArrayField is MissingType, reason="ArrayField should exist")
def test_array_field_contains_empty_list(schema):
    """
    Test contains filter on a array field of string.
    """

    query = """
    query {
        events (tags_Contains: []) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    result = schema.execute(query)
    assert not result.errors
    assert result.data["events"]["edges"] == [
        {"node": {"name": "Live Show"}},
        {"node": {"name": "Musical"}},
        {"node": {"name": "Ballet"}},
        {"node": {"name": "Speech"}},
    ]
