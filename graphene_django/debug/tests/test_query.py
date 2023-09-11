import pytest
from graphql_sync_dataloaders import DeferredExecutionContext

import graphene
from graphene.relay import Node
from graphene_django import DjangoConnectionField, DjangoObjectType

from ...tests.models import Reporter
from ..middleware import DjangoDebugMiddleware
from ..types import DjangoDebug


class context:
    pass


@pytest.fixture(autouse=True)
def execution_context_class(execution_context_class):
    """
    Fixture to test with custom `execution_context_class`
    """
    return execution_context_class


def test_should_query_field():
    r1 = Reporter(last_name="ABA")
    r1.save()
    r2 = Reporter(last_name="Griffin")
    r2.save()

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            fields = "__all__"

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)
        debug = graphene.Field(DjangoDebug, name="_debug")

        def resolve_reporter(self, info, **args):
            return Reporter.objects.first()

    query = """
        query ReporterQuery {
          reporter {
            lastName
          }
          _debug {
            sql {
              rawSql
            }
          }
        }
    """
    expected = {
        "reporter": {"lastName": "ABA"},
        "_debug": {"sql": [{"rawSql": str(Reporter.objects.order_by("pk")[:1].query)}]},
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(
        query, context_value=context(), middleware=[DjangoDebugMiddleware()]
    )
    assert not result.errors
    assert result.data == expected


@pytest.mark.parametrize("max_limit", [None, 100])
def test_should_query_nested_field(
    django_assert_num_queries, execution_context_class, graphene_settings, max_limit
):
    graphene_settings.RELAY_CONNECTION_MAX_LIMIT = max_limit

    r1 = Reporter(last_name="ABA")
    r1.save()
    r2 = Reporter(last_name="Griffin")
    r2.save()
    r2.pets.add(r1)
    r1.pets.add(r2)

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            fields = "__all__"

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)
        debug = graphene.Field(DjangoDebug, name="_debug")

        def resolve_reporter(self, info, **args):
            return Reporter.objects.first()

    query = """
        query ReporterQuery {
          reporter {
            lastName
            pets { edges { node {
              lastName
              pets { edges { node { lastName } } }
            } } }
          }
          _debug {
            sql {
              rawSql
            }
          }
        }
    """
    expected = {
        "reporter": {
            "lastName": "ABA",
            "pets": {
                "edges": [
                    {
                        "node": {
                            "lastName": "Griffin",
                            "pets": {"edges": [{"node": {"lastName": "ABA"}}]},
                        }
                    }
                ]
            },
        }
    }
    schema = graphene.Schema(query=Query)
    with django_assert_num_queries(3):
        result = schema.execute(
            query,
            context_value=context(),
            middleware=[DjangoDebugMiddleware()],
            execution_context_class=execution_context_class,
        )
    assert not result.errors
    if execution_context_class is not DeferredExecutionContext:
        # dataloaders breaks `_debug` middleware
        query = str(Reporter.objects.order_by("pk")[:1].query)
        assert result.data["_debug"]["sql"][0]["rawSql"] == query
        assert "tests_reporter_pets" in result.data["_debug"]["sql"][1]["rawSql"]
        assert "tests_reporter_pets" in result.data["_debug"]["sql"][2]["rawSql"]
        assert len(result.data["_debug"]["sql"]) == 3

    assert result.data["reporter"] == expected["reporter"]


def test_should_query_list():
    r1 = Reporter(last_name="ABA")
    r1.save()
    r2 = Reporter(last_name="Griffin")
    r2.save()

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            fields = "__all__"

    class Query(graphene.ObjectType):
        all_reporters = graphene.List(ReporterType)
        debug = graphene.Field(DjangoDebug, name="_debug")

        def resolve_all_reporters(self, info, **args):
            return Reporter.objects.all()

    query = """
        query ReporterQuery {
          allReporters {
            lastName
          }
          _debug {
            sql {
              rawSql
            }
          }
        }
    """
    expected = {
        "allReporters": [{"lastName": "ABA"}, {"lastName": "Griffin"}],
        "_debug": {"sql": [{"rawSql": str(Reporter.objects.all().query)}]},
    }
    schema = graphene.Schema(query=Query)
    result = schema.execute(
        query, context_value=context(), middleware=[DjangoDebugMiddleware()]
    )
    assert not result.errors
    assert result.data == expected


@pytest.mark.parametrize("max_limit", [None, 100])
def test_should_query_connection(
    django_assert_num_queries, execution_context_class, graphene_settings, max_limit
):
    graphene_settings.RELAY_CONNECTION_MAX_LIMIT = max_limit

    r1 = Reporter(last_name="ABA")
    r1.save()
    r2 = Reporter(last_name="Griffin")
    r2.save()

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            fields = "__all__"

    class Query(graphene.ObjectType):
        all_reporters = DjangoConnectionField(ReporterType)
        debug = graphene.Field(DjangoDebug, name="_debug")

        def resolve_all_reporters(self, info, **args):
            return Reporter.objects.all()

    query = """
        query ReporterQuery {
          allReporters(first:1) {
            edges {
              node {
                lastName
              }
            }
          }
          _debug {
            sql {
              rawSql
            }
          }
        }
    """
    expected = {"allReporters": {"edges": [{"node": {"lastName": "ABA"}}]}}
    schema = graphene.Schema(query=Query)
    with django_assert_num_queries(1) as captured:
        result = schema.execute(
            query,
            context_value=context(),
            middleware=[DjangoDebugMiddleware()],
            execution_context_class=execution_context_class,
        )
    assert not result.errors
    assert result.data["allReporters"] == expected["allReporters"]
    if execution_context_class is not DeferredExecutionContext:
        # dataloaders breaks `_debug` middleware
        assert len(result.data["_debug"]["sql"]) == 1
        query = str(Reporter.objects.all()[:2].query)
        assert result.data["_debug"]["sql"][0]["rawSql"] == query

    assert len(captured.captured_queries) == 1


@pytest.mark.parametrize("max_limit", [None, 100])
def test_should_query_connectionfilter(
    django_assert_num_queries, execution_context_class, graphene_settings, max_limit
):
    graphene_settings.RELAY_CONNECTION_MAX_LIMIT = max_limit

    from ...filter import DjangoFilterConnectionField

    r1 = Reporter(last_name="ABA")
    r1.save()
    r2 = Reporter(last_name="Griffin")
    r2.save()

    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            fields = "__all__"

    class Query(graphene.ObjectType):
        all_reporters = DjangoFilterConnectionField(ReporterType, fields=["last_name"])
        s = graphene.String(resolver=lambda *_: "S")
        debug = graphene.Field(DjangoDebug, name="_debug")

        def resolve_all_reporters(self, info, **args):
            return Reporter.objects.all()

    query = """
        query ReporterQuery {
          allReporters(first:1) {
            edges {
              node {
                lastName
              }
            }
          }
          _debug {
            sql {
              rawSql
            }
          }
        }
    """
    expected = {"allReporters": {"edges": [{"node": {"lastName": "ABA"}}]}}
    schema = graphene.Schema(query=Query)
    with django_assert_num_queries(1) as captured:
        result = schema.execute(
            query,
            context_value=context(),
            middleware=[DjangoDebugMiddleware()],
            execution_context_class=execution_context_class,
        )
    assert not result.errors
    assert result.data["allReporters"] == expected["allReporters"]
    query = str(Reporter.objects.all()[:2].query)
    if execution_context_class is not DeferredExecutionContext:
        # dataloaders breaks `_debug` middleware
        assert len(result.data["_debug"]["sql"]) == 1
        assert result.data["_debug"]["sql"][0]["rawSql"] == query

    assert len(captured.captured_queries) == 1


def test_should_query_stack_trace():
    class ReporterType(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)
            fields = "__all__"

    class Query(graphene.ObjectType):
        reporter = graphene.Field(ReporterType)
        debug = graphene.Field(DjangoDebug, name="_debug")

        def resolve_reporter(self, info, **args):
            raise Exception("caught stack trace")

    query = """
        query ReporterQuery {
          reporter {
            lastName
          }
          _debug {
            exceptions {
              message
              stack
            }
          }
        }
    """
    schema = graphene.Schema(query=Query)
    result = schema.execute(
        query, context_value=context(), middleware=[DjangoDebugMiddleware()]
    )
    assert result.errors
    assert len(result.data["_debug"]["exceptions"])
    debug_exception = result.data["_debug"]["exceptions"][0]
    assert debug_exception["stack"].count("\n") > 1
    assert "test_query.py" in debug_exception["stack"]
    assert debug_exception["message"] == "caught stack trace"
