#-*- coding: utf-8 -*-
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponseRedirect

from questions_answers.models import Question, Answer, QuestionTag
from forms import ContactForm


def search_view(request):
    """ Поиск по сайту """

    search = ''
    report = ''
    results = []

    if request.GET['search']:
        if 3 > len(request.GET['search']) > 0:
            report = 'Нет результатов по вашему запросу.'
        if len(request.GET['search']) > 2:
            search = request.GET['search']
            search = search.split()

            for word in search:
                results.extend(Question.objects.filter((
                    Q(title__icontains=word) | Q(
                        question_text__icontains=word))))
                results.extend(
                    Answer.objects.filter(answer_text__icontains=word))
                results.extend(
                    QuestionTag.objects.filter(name__icontains=word))

            # Удаляет повторы в списке и сохраняет порядок
            results = sorted(set(results), key=results.index)

            if not results:
                report = 'Нет результатов по вашему запросу.'
    else:
        results = []
        report = 'Вы не ввели данные в строку запроса'
    ctx = {'results': results, 'report': report, 'search': search}

    return render_to_response('search.html', ctx,
                              context_instance=RequestContext(request))


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ваше сообщение отправлено.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        form = ContactForm(request.user)
    return render(request, 'contact.html', {'form': form})