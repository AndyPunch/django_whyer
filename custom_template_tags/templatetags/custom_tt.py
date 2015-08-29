import re
from datetime import datetime, date
from django import template
from django.utils.translation import ugettext as _
from django.template import defaultfilters

register = template.Library()

@register.simple_tag
def active(path, pattern):
    if re.search(pattern, path):
        return "active"
    return ''

@register.simple_tag
def a_active(path, pattern):
    if re.search(pattern, path):
        return "a_active"
    return ''

@register.filter(expects_localtime=True)
def mynaturalday(value, arg=None):
    try:
        tzinfo = getattr(value, 'tzinfo', None)
        value = date(value.year, value.month, value.day)
    except AttributeError:
        return value
    except ValueError:
        return value
    today = datetime.now(tzinfo).date()
    delta = value - today
    if delta.days == 0:
        return _('today')
    elif delta.days == 1:
        return _('tomorrow')
    elif delta.days == -1:
        return _('yesterday')
    #elif delta.days > 1:
        #return value.day
    return defaultfilters.date(value, arg)