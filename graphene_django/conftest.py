import pytest

from graphene_django.settings import graphene_settings as gsettings

from graphql_sync_dataloaders import DeferredExecutionContext

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


@pytest.fixture(params=[(True, DeferredExecutionContext), (False, None)], autouse=True)
def use_dataloaders(request):
    settings = dict(gsettings.__dict__)
    gsettings.USE_DATALOADERS = request.param[0]
    yield request.param[1]
    gsettings.__dict__ = settings
