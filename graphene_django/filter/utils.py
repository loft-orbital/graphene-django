import six

import graphene

from django import forms

from django_filters.utils import get_model_field, get_field_parts
from django_filters.filters import Filter, BaseCSVFilter

from .filterset import custom_filterset_factory, setup_filterset
from .filters import InFilter, RangeFilter
from ..forms import GlobalIDFormField, GlobalIDMultipleChoiceField


def get_filtering_args_from_filterset(filterset_class, type):
    """
    Inspect a FilterSet and produce the arguments to pass to a Graphene Field.
    These arguments will be available to filter against in the GraphQL API.
    """
    from ..forms.converter import convert_form_field

    args = {}
    model = filterset_class._meta.model
    for name, filter_field in six.iteritems(filterset_class.base_filters):
        filter_type = filter_field.lookup_expr

        if name in filterset_class.declared_filters:
            # Get the filter field from the explicitly declared filter
            form_field = filter_field.field
            field = convert_form_field(form_field)
        else:
            # Get the filter field with no explicit type declaration
            required = filter_field.extra.get("required", False)
            if filter_type == "isnull":
                field = graphene.Boolean(required=required)
            else:
                model_field = get_model_field(model, filter_field.field_name)
                field = None
                form_field = None

                # Get the form field either from:
                #  1. the formfield corresponding to the model field
                #  2. the field defined on filter
                if hasattr(model_field, "formfield"):
                    form_field = model_field.formfield(required=required)
                if not form_field:
                    form_field = filter_field.field

                # First try to get the matching field type from the GraphQL DjangoObjectType
                if model_field:
                    registry = type._meta.registry
                    if isinstance(form_field, forms.ModelChoiceField) or \
                        isinstance(form_field, forms.ModelMultipleChoiceField) or \
                        isinstance(form_field, GlobalIDMultipleChoiceField) or \
                        isinstance(form_field, GlobalIDFormField):
                        # Foreign key have dynamic types and filtering on a foreign key actually means filtering on its ID.
                        object_type = registry.get_type_for_model(model_field.related_model)
                        model_field_name = "id"
                    else:
                        object_type = registry.get_type_for_model(model_field.model)
                        model_field_name = model_field.name
                    if object_type:
                        object_type_field = object_type._meta.fields.get(model_field_name)
                        if object_type_field:
                            object_type_field_type = object_type_field.type
                            if hasattr(object_type_field_type, "of_type"):
                                object_type_field_type = object_type_field_type.of_type
                            try:
                                field = object_type_field_type(
                                    description=getattr(model_field, "help_text", ""),
                                    required=required,
                                )
                            except Exception:
                                # This method does not work for all types (like custom or dynamic types)
                                # so we fallback on trying to convert the form field.
                                pass

                if not field:
                    # Fallback on converting the form field
                    field = convert_form_field(form_field)

        if filter_type in {"in", "range", "contains", "overlap"} and \
            (issubclass(filter_field.__class__, InFilter) or issubclass(filter_field.__class__, RangeFilter)):
            # Replace InFilter/RangeFilter filters (`in`, `range`, `contains`, `overlap`) argument type to be a list of
            # the same type as the field.  See comments in
            # `replace_csv_filters` method for more details.
            field = graphene.List(field.get_type())

        field_type = field.Argument()

        field_type.description = filter_field.label
        args[name] = field_type

    return args


def get_filterset_class(filterset_class, **meta):
    """
    Get the class to be used as the FilterSet.
    """
    if filterset_class:
        # If were given a FilterSet class, then set it up.
        graphene_filterset_class = setup_filterset(filterset_class)
    else:
        # Otherwise create one.
        graphene_filterset_class = custom_filterset_factory(**meta)

    replace_csv_filters(graphene_filterset_class)
    return graphene_filterset_class


def replace_csv_filters(filterset_class):
    """
    Replace the "in", "contains", "overlap" and "range" filters (that are not explicitly declared) to not be BaseCSVFilter (BaseInFilter, BaseRangeFilter) objects anymore
    but regular Filter objects that simply use the input value as filter argument on the queryset.

    This is because those BaseCSVFilter are expecting a string as input with comma separated value but with GraphQl we
    can actually have a list as input and have a proper type verification of each value in the list.

    See issue https://github.com/graphql-python/graphene-django/issues/1068.
    """
    for name, filter_field in six.iteritems(filterset_class.base_filters):
        # Do not touch any declared filters
        if name in filterset_class.declared_filters:
            continue

        filter_type = filter_field.lookup_expr
        if filter_type in {"in", "contains", "overlap"}:

            filterset_class.base_filters[name] = InFilter(
                field_name=filter_field.field_name,
                lookup_expr=filter_field.lookup_expr,
                label=filter_field.label,
                method=filter_field.method,
                exclude=filter_field.exclude,
                **filter_field.extra
            )

        elif filter_type == "range":

            filterset_class.base_filters[name] = RangeFilter(
                field_name=filter_field.field_name,
                lookup_expr=filter_field.lookup_expr,
                label=filter_field.label,
                method=filter_field.method,
                exclude=filter_field.exclude,
                **filter_field.extra
            )
