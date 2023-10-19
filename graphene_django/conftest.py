import pytest
from graphql_sync_dataloaders import DeferredExecutionContext

from graphene_django.settings import graphene_settings as gsettings

from .registry import reset_global_registry


@pytest.fixture(autouse=True)
def reset_registry_fixture(db):
    yield None
    reset_global_registry()


@pytest.fixture()
def graphene_settings():
    settings = dict(gsettings.__dict__)
    yield gsettings
    gsettings.__dict__ = settings


@pytest.fixture(
    params=[(True, DeferredExecutionContext), (False, None)],
    ids=["dataloaders_enabled", "dataloaders_disabled"],
)
def use_dataloaders(request):
    """
    Fixture to test with and without dataloaders enabled.
    """

    use_dataloaders, execution_context = request.param

    settings = dict(gsettings.__dict__)
    gsettings.USE_DATALOADERS = use_dataloaders
    yield execution_context
    gsettings.__dict__ = settings
