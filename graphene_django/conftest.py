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
    ids=["dataloader_enabled", "dataloader_disabled"],
)
def use_dataloaders(request):
    """
    Fixture to test with and without dataloaders enabled.
    """

    USE_DATALOADERS, execution_context = request.param

    settings = dict(gsettings.__dict__)
    gsettings.USE_DATALOADERS = USE_DATALOADERS
    yield execution_context
    gsettings.__dict__ = settings
