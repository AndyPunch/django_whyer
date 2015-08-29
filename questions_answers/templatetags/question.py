#-*- coding:utf-8 -*-
from django import template
from questions_answers.models import SavedQuestion
from django.utils.safestring import mark_safe
from questions_answers.views import get_active_questions


register = template.Library()

@register.filter
def isfollow_question(question, user):
    try:
        SavedQuestion.objects.get(question=question, user=user)
        return True
    except SavedQuestion.DoesNotExist:
        return False


@register.filter
def rupluralize(value, arg):
    args = arg.split(",")
    number = abs(int(value))
    a = number % 10
    b = number % 100
    if (a == 1) and (b != 11):
        return args[0]
    elif (a >= 2) and (a <= 4) and ((b < 10 ) or (b >= 20)):
        return args[1]
    else:
        return args[2]

@register.filter
def highlight(text, words):
    for i in words:
        capitalized = i.capitalize()
        text = mark_safe(text.replace(capitalized, "<span style='background-color: #E0EAF1'>%s</span>" % capitalized)
        .replace(i, "<span style='background-color: #E0EAF1'>%s</span>" % i))
    return text

@register.inclusion_tag('misc/questions/active_questions_for_sidebar.html')
def sidebar_data_with_active_questions():
    active_questions = get_active_questions()
    return {'active_questions': active_questions}