class MissingType:
    def __init__(self, *args, **kwargs):
        pass


try:
    # Postgres fields are only available in Django with psycopg2 installed
    # and we cannot have psycopg2 on PyPy
    from django.contrib.postgres.fields import (
        ArrayField,
        HStoreField,
        IntegerRangeField,
        RangeField,
    )
    from django.db.models import Choices

except ImportError:
    IntegerRangeField, ArrayField, HStoreField, RangeField, Choices = (MissingType,) * 5

try:
    from django.db.models import JSONField
except ImportError:
    try:
        from django.contrib.postgres.fields import JSONField
    except ImportError:
        JSONField = MissingType
