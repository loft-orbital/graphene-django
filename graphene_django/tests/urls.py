from django.urls import path

from graphene_django.settings import graphene_settings

from graphql_sync_dataloaders import DeferredExecutionContext

from ..views import GraphQLView

urlpatterns = [
    path("graphql/batch", GraphQLView.as_view(batch=True)),
    path("graphql", GraphQLView.as_view(
            graphiql=True,
            execution_context_class=DeferredExecutionContext
            if graphene_settings.USE_DATALOADERS
            else None,
        ),
    ),
]
