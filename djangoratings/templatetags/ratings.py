"""
Template tags for Django
"""
# TODO: add in Jinja tags if Coffin is available

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from djangoratings.views import _rating_widget

register = template.Library()


class RatingByRequestNode(template.Node):
    def __init__(self, request, obj, context_var):
        self.request = request
        split = obj.rsplit('.', 1)
        self.field_name = split[-1]
        self.obj = split[0]
        self.context_var = context_var
    
    def render(self, context):
        try:
            request = template.resolve_variable(self.request, context)
            obj = template.resolve_variable(self.obj, context)
            field = getattr(obj, self.field_name)
        except (template.VariableDoesNotExist, AttributeError):
            return ''
        vote = field.get_rating_for_user(request.user, request.META['REMOTE_ADDR'], request.COOKIES)
        context[self.context_var] = vote
        return ''


def do_rating_by_request(parser, token):
    """
    Retrieves the ``Vote`` cast by a user on a particular object and
    stores it in a context variable. If the user has not rated, the
    context variable will be ``None``.
    
    Example usage::

        {% rating on instance.field as vote %}
    
        {% rating_by_request request on instance.field as vote %}
    """
    
    bits = token.contents.split()
    if len(bits) == 5:
        bits.insert(1, 'request')
    elif len(bits) != 6:
        raise template.TemplateSyntaxError("'%s' tag takes exactly five arguments" % bits[0])
    if bits[2] != 'on':
        raise template.TemplateSyntaxError("second argument to '%s' tag must be 'on'" % bits[0])
    if bits[4] != 'as':
        raise template.TemplateSyntaxError("fourth argument to '%s' tag must be 'as'" % bits[0])
    return RatingByRequestNode(bits[1], bits[3], bits[5])
register.tag('rating_by_request', do_rating_by_request)
register.tag('rating', do_rating_by_request)


class RatingByUserNode(template.Node):
    def __init__(self, user, obj, context_var):
        self.user = user
        split = obj.rsplit('.', 1)
        self.field_name = split[-1]
        self.obj = split[0]
        self.context_var = context_var
    
    def render(self, context):
        try:
            user = template.resolve_variable(self.user, context)
            obj = template.resolve_variable(self.obj, context)
            field = getattr(obj, self.field_name)
        except template.VariableDoesNotExist:
            return ''
        vote = field.get_rating_for_user(user)
        context[self.context_var] = vote
        return ''


def do_rating_by_user(parser, token):
    """
    Retrieves the ``Vote`` cast by a user on a particular object and
    stores it in a context variable. If the user has not rated, the
    context variable will be ``None``.
    
    Example usage::
    
        {% rating_by_user user on instance.field as vote %}
    """
    
    bits = token.contents.split()
    if len(bits) != 6:
        raise template.TemplateSyntaxError("'%s' tag takes exactly five arguments" % bits[0])
    if bits[2] != 'on':
        raise template.TemplateSyntaxError("second argument to '%s' tag must be 'on'" % bits[0])
    if bits[4] != 'as':
        raise template.TemplateSyntaxError("fourth argument to '%s' tag must be 'as'" % bits[0])
    return RatingByUserNode(bits[1], bits[3], bits[5])
register.tag('rating_by_user', do_rating_by_user)


class RatingWidgetByRequestNode(template.Node):
    def __init__(self, request, obj, widget_template):
        self.request = request
        split = obj.rsplit('.', 1)
        self.field_name = split[-1]
        self.obj = split[0]
        self.widget_template = widget_template

    def render(self, context):
        try:
            request = template.resolve_variable(self.request, context)
            obj = template.resolve_variable(self.obj, context)
            field = getattr(obj, self.field_name)
            widget_template = template.resolve_variable(self.widget_template, context) if self.widget_template else field.field.widget_template
        except (template.VariableDoesNotExist, AttributeError):
            return ''
        had_voted = field.get_rating_for_user(request.user, request.META['REMOTE_ADDR'], request.COOKIES)
        return render_to_string(widget_template, _rating_widget(obj, field, had_voted), context)


def do_rating_widget_by_request(parser, token):
    """
    Retrieves the ``Vote`` cast by a user on a particular object and
    outputs the widget.
    
    Example usage::
    
        {% rating_widget on instance.field %}

        {% rating_widget_by_request request on instance.field %}

        {% rating_widget_by_request request on instance.field using "template_name.html" %}
    """

    bits = token.contents.split()

    if len(bits) > 1 and bits[1] == 'on':
        bits.insert(1, 'request')

    if len(bits) not in (3, 4, 6):
        raise template.TemplateSyntaxError("'%s' tag takes exactly two, three or five arguments" % bits[0])

    if bits[2] != 'on':
        raise template.TemplateSyntaxError("first or second argument to '%s' tag must be 'on'" % bits[0])

    if len(bits) > 3 and bits[4] != 'using':
        raise template.TemplateSyntaxError("fourth argument to '%s' tag must be 'using'" % bits[0])

    request = bits[1]
    field = bits[3]

    if len(bits) == 6:
        widget_template = bits[5]
    else:
        widget_template = None

    return RatingWidgetByRequestNode(request, field, widget_template)
register.tag('rating_widget_by_request', do_rating_widget_by_request)
register.tag('rating_widget', do_rating_widget_by_request)


class RatingWidgetByUserNode(template.Node):
    def __init__(self, user, obj):
        self.user = user
        split = obj.rsplit('.', 1)
        self.field_name = split[-1]
        self.obj = split[0]

    def render(self, context):
        try:
            user = template.resolve_variable(self.user, context)
            obj = template.resolve_variable(self.obj, context)
            field = getattr(obj, self.field_name)
        except (template.VariableDoesNotExist, AttributeError):
            return ''
        had_voted = field.get_rating_for_user(user)
        return render_to_string(field.field.widget_template, _rating_widget(obj, field, had_voted), context)


def do_rating_widget_by_user(parser, token):
    """
    Retrieves the ``Vote`` cast by a user on a particular object and
    outputs the widget.
    
    Example usage::
    
        {% rating_widget_by_user user on instance.field %}
    """

    bits = token.contents.split()
    if len(bits) == 3:
        bits.insert(0, 'request')
    elif len(bits) != 4:
        raise template.TemplateSyntaxError("'%s' tag takes exactly five arguments" % bits[0])
    if bits[2] != 'on':
        raise template.TemplateSyntaxError("second argument to '%s' tag must be 'on'" % bits[0])
    return RatingWidgetByRequestNode(bits[1], bits[3])
register.tag('rating_widget_by_user', do_rating_widget_by_user)


def _rates(rate, out_of, stars):
    stars = float(stars)
    if float(rate) and float(out_of):
        rate = (float(rate) / float(out_of)) * stars
        if rate > stars:
            rate = stars
    else:
        rate = 0
    stars *= 16
    rate *= 16
    return '<span class="rate_stars" style="width:%dpx"><span style="width:%dpx"></span></span>' % (int(stars), int(rate))


@register.simple_tag
def rates(rate, out_of=5, stars=5):
    return _rates(rate, out_of, stars)


# Filters


@register.filter
def rating_display(rating):
    """
    Given a rating returns a stars field.

    Example usage::

        {{ rating|rating_display }}
    """
    cnt = rating.field.range_upper - rating.field.range_lower + 1
    return mark_safe(_rates(rating.get_rating(), cnt, cnt))
