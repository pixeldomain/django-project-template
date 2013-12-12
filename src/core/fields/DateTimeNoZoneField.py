import datetime
from django.utils.timezone import utc
from django.db import models
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^core\.fields\.DateTimeNoZoneField"])
except ImportError:
    pass

class DateTimeNoZoneField(models.DateTimeField):

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
        value_aware = value
        if isinstance(value, datetime.datetime):
            value_aware = value.replace(tzinfo=utc)
        return super(DateTimeNoZoneField, self).to_python(value_aware)
