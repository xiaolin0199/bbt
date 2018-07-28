# coding=utf-8
from django.forms import Field
from django.forms import ValidationError


class CharListField(Field):

    def __init__(self, *args, **kwargs):
        return super(CharListField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not isinstance(value, list):
            raise ValidationError('invalid field type')
        return value
