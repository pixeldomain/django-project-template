import datetime
from dateutil import tz
from django.db import models
from django.conf import settings
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^core\.fields\.DateTimeNoZoneField"])
except ImportError:
    pass


class DateTimeNoZoneField(models.DateTimeField):
    """Creates a DB datetime field that is TZ naive."""

    description = "Date (with time and no timezone)"

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        super(DateTimeNoZoneField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return 'datetime'
        else:
            return 'timestamp'

    def to_python(self, value):
        if isinstance(value, datetime.datetime):
            value = value.replace(tzinfo=tz.gettz('UTC')).astimezone(
                tz.gettz(settings.TIME_ZONE))
        return super(DateTimeNoZoneField, self).to_python(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        return connection.ops.value_to_db_datetime(value)
