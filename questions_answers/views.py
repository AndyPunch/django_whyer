#-*- coding:utf-8 -*-
import re
from itertools import chain

from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.db.models import Count
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.views.generic import ListView, DetailView, RedirectView, CreateView
from django.views.generic import DeleteView, UpdateView

from guardian.mixins import LoginRequiredMixin

from djangoratings.views import AddRatingView

from models import Question, Answer, SavedQuestion, QuestionTag
from comments.models import Comment
from forms import QuestionCreateForm, AnswerCreateForm, QuestionCommentForm, AnswerCommentForm


class QuestionListView(ListView):
    context_object_name = 'question_list'
    model = Question
    paginate_by = 3

    def get_queryset(self):
        if 'featured' in self.request.GET:
            return Question.objects.annotate(
                savedquestion_count=Count('savedquestion')).filter(
                savedquestion_count__gt=0) \
                .order_by('-savedquestion_count')
        elif 'unanswered' in self.request.GET:
            return Question.objects.filter(answer__isnull=True).order_by(
                '-created_at')
        elif 'votes' in self.request.GET:
            return Question.objects.all().order_by('-rating_score')
        else:
            return Question.objects.all().order_by('-created_at')

    def get_template_names(self):
        """ Для правильной постраничной навигации """

        if 'featured' in self.request.GET:
            template_name = 'questions_answers/question_featured.html'
        elif 'unanswered' in self.request.GET:
            template_name = 'questions_answers/question_unanswered.html'
        elif 'votes' in self.request.GET:
            template_name = 'questions_answers/question_votes.html'
        else:
            template_name = 'questions_answers/question_list.html'
        return template_name

    def get_context_data(self, **kwargs):
        context = super(QuestionListView, self).get_context_data(**kwargs)
        unanswered_questions = Question.objects.filter(
            answer__isnull=True).order_by('-created_at')
        votes_question = Question.objects.all().order_by('-rating_score')
        featured_questions = Question.objects.annotate(
            savedquestion_count=Count('savedquestion')).filter(
            savedquestion_count__gt=0).order_by('-savedquestion_count')
        favorite_questions = Question.objects.all().annotate(
            savedquestion_count=Count('savedquestion')).order_by("title")
        context['favorite_questions'] = favorite_questions
        context['unanswered_questions'] = unanswered_questions
        context['featured_questions'] = featured_questions
        context['votes_question'] = votes_question
        return context


class QuestionDetailView(DetailView):
    model = Question
    context_object_name = 'question_detail'
    template_name = 'questions_answers/question_detail.html'

    def get_context_data(self, **kwargs):
        context = super(QuestionDetailView, self).get_context_data(**kwargs)
        current_question = get_object_or_404(Question,
                                             slug=self.kwargs['slug'])
        favorite_questions = Question.objects.all().order_by("title").annotate(
            savedquestion_count=Count('savedquestion'))
        related_questions = Question.objects.filter(
            question_tag__id__in=current_question.question_tag.distinct())
        related_questions = set(related_questions)
        context['related_questions'] = related_questions
        context['favorite_questions'] = favorite_questions
        context['comment_question_form'] = QuestionCommentForm(
            instance=current_question)
        context['comment_answer_form'] = AnswerCommentForm(
            instance=current_question)
        context['form'] = AnswerCreateForm(self, self.request.user,
                                           instance=current_question)
        return context

    def get_object(self, **kwargs):
        """ Считает просмотры """

        question = super(QuestionDetailView, self).get_object()
        question.view_count += 1
        question.save()
        return question


class QuestionCreateView(CreateView):
    form_class = QuestionCreateForm
    template_name = 'questions_answers/ask_question_form.html'

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.author = self.request.user
        instance.save()
        tags = form.cleaned_data['tag'].lower()

        # чтобы пользователь не заморачивался чем разделять теги
        tags = re.sub('[.!,:;]', ' ', tags)

        for eachtag in tags:
            tag, created = QuestionTag.objects.get_or_create(
                name=eachtag.strip())
            tag.save()
            instance.question_tag.add(tag)
        form.save_m2m()
        return HttpResponseRedirect(
            reverse('question_complete', kwargs={'slug': instance.slug}))

    def get_context_data(self, **kwargs):
        """ Для автодополнения тегов"""

        context = super(QuestionCreateView, self).get_context_data(**kwargs)
        tags_list = [tag.encode("utf-8") for tag in
                     QuestionTag.objects.values_list('name', flat=True)]
        tags_string = ''
        quote = '"'
        for tag in tags_list:
            tags_string += quote + tag + quote + ","
        context['tags'] = tags_string
        return context


class QuestionUpdateView(UpdateView):
    form_class = QuestionCreateForm
    model = Question
    template_name = 'questions_answers/question_edit.html'

    def get_object(self, *args, **kwargs):
        obj = super(QuestionUpdateView, self).get_object(*args, **kwargs)
        if obj.author != self.request.user:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        context = super(QuestionUpdateView, self).get_context_data(**kwargs)
        tags_list = [tag.encode("utf-8") for tag in
                     QuestionTag.objects.values_list('name', flat=True)]
        tags_string = ''
        quote = '"'
        for tag in tags_list:
            tags_string += quote + tag + quote + ","
        context['tags'] = tags_string
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.author = self.request.user
        instance.save()
        tags = form.cleaned_data['tag'].lower()
        tags = re.sub('[.!,:;]', ' ', tags)
        tags = tags.split()
        for eachtag in tags:
            tag, created = QuestionTag.objects.get_or_create(
                name=eachtag.strip())
            tag.save()
            instance.question_tag.add(tag)
        form.save_m2m()
        return HttpResponseRedirect(
            reverse('question_complete', kwargs={'slug': instance.slug}))


class QuestionDeleteView(DeleteView):
    model = Question
    success_url = reverse_lazy('question_list')
    template_name = 'questions_answers/question_delete.html'

    def get_object(self, queryset=None):
        obj = super(QuestionDeleteView, self).get_object()
        if not obj.author == self.request.user:
            raise Http404
        return obj


def question_complete(request, slug=None):
    question = get_object_or_404(Question, slug=slug)
    favorite_questions = Question.objects.all().order_by("title").annotate(
        savedquestion_count=Count('savedquestion'))
    related_questions = Question.objects.filter(
        question_tag__id__in=question.question_tag.distinct())
    related_questions = set(related_questions)
    context = {}
    context['question_detail'] = question
    context['related_questions'] = related_questions
    context['favorite_questions'] = favorite_questions
    return render_to_response('questions_answers/question_complete.html',
                              context,
                              context_instance=RequestContext(request))


class AnswerCreateView(CreateView):
    form_class = AnswerCreateForm
    template_name = 'questions_answers/question_detail.html'

    def get_form(self, form_class):
        current_question = get_object_or_404(Question,
                                             slug=self.kwargs['slug'])
        form = AnswerCreateForm(self.request.user, current_question,
                                self.request.POST)
        return form

    def get_context_data(self, **kwargs):
        context = super(AnswerCreateView, self).get_context_data(**kwargs)
        current_question = get_object_or_404(Question,
                                             slug=self.kwargs['slug'])
        answer_form = self.get_form(form_class=AnswerCreateForm)
        context['comment_question_form'] = QuestionCommentForm(
            instance=current_question)
        context['question_detail'] = current_question
        context['comment_answer_form'] = AnswerCommentForm(
            instance=current_question)
        context['form'] = answer_form
        return context

    def form_valid(self, form):
        current_question = get_object_or_404(Question,
                                             slug=self.kwargs['slug'])
        instance = form.save(commit=False)
        instance.question = current_question
        instance.author = self.request.user
        instance.save()
        return HttpResponseRedirect(
            reverse('question_detail', kwargs={'slug': current_question.slug}))


@login_required
def rate_question(request, object_id, score):
    model = 'question'
    app_label = 'questions_answers'
    field_name = 'rating'
    try:
        content_type = ContentType.objects.get(model=model,
                                               app_label=app_label)
    except ContentType.DoesNotExist:
        raise Http404('Invalid `model` or `app_label`.')
    params = {
        'content_type_id': content_type.id,
        'object_id': object_id,
        'field_name': field_name,
        'score': score,
    }

    #question = get_object_or_404(Question, id=object_id)
    #if request.user == question.author:

    #messages.error(request, ' Вы не можете голосовать за свой вопрос')
    #return HttpResponseRedirect(request.META['HTTP_REFERER'])
    #else:
    response = AddRatingView()(request, **params)
    if response.status_code == 200:
        if response.content == 'Vote recorded.':
            messages.success(request, 'Спасибо! Ваш голос учтён')
            #else
            #messages.error(request, 'Sorry, Something went wrong')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def rate_answer(request, object_id, score):
    model = 'answer'
    app_label = 'questions_answers'
    field_name = 'rating'
    try:
        content_type = ContentType.objects.get(model=model,
                                               app_label=app_label)

    except ContentType.DoesNotExist:
        raise Http404('Invalid `model` or `app_label`.')
    params = {
        'content_type_id': content_type.id,
        'object_id': object_id,
        'field_name': field_name,
        'score': score,
    }
    #answer = get_object_or_404(Answer, id=object_id)
    #if request.user == answer.author:
    #messages.error(request, ' Вы не можете голосовать за свой ответ')
    #return HttpResponseRedirect(request.META['HTTP_REFERER'])
    response = AddRatingView()(request, **params)
    if response.status_code == 200:
        if response.content == 'Vote recorded.':
            messages.success(request, 'Спасибо! Ваш голос учтён')
            #else:

            #messages.error(request, 'Sorry, Something went wrong')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class QuestionSaveView(RedirectView):
    permanent = False

    def get_redirect_url(self, slug):
        question = get_object_or_404(Question, slug=slug)
        try:
            sq = SavedQuestion.objects.get(user=self.request.user,
                                           question=question)
            sq.delete()
        except SavedQuestion.DoesNotExist:
            SavedQuestion.objects.create(user=self.request.user,
                                         question=question)
        if self.request.META.get('HTTP_REFERER'):
            return self.request.META.get('HTTP_REFERER')
        else:
            return reverse_lazy('question_detail', kwargs={'slug': slug})


class QuestionTagListView(ListView):
    context_object_name = 'question_list'
    template_name = 'questions_answers/question_tags.html'
    paginate_by = 5

    def get_queryset(self):
        slug_received = self.kwargs['slug']
        tag = get_object_or_404(QuestionTag, slug=slug_received)
        return tag.question_set.all().order_by('created_at')

    def get_context_data(self, **kwargs):
        context = super(QuestionTagListView, self).get_context_data(**kwargs)
        slug_received = self.kwargs['slug']
        tags = get_object_or_404(QuestionTag, slug=slug_received)

        context['question_tags'] = tags
        return context


class QuestionTagAllListView(ListView):
    context_object_name = 'rows'
    template_name = 'questions_answers/question_tags_list.html'
    paginate_by = 2

    def get_queryset(self):
        if 'search' in self.request.GET:
            search_text = self.request.GET.get('search')
            question_tags = QuestionTag.objects.filter(
                name__contains=search_text)

            # для правильного распределения ячеек таблицы
            rows = [question_tags[x:x + 4] for x in
                    range(0, len(question_tags), 4)]
            return rows
        else:
            tags = QuestionTag.objects.all()
            rows = [tags[x:x + 4] for x in range(0, len(tags), 4)]
            return rows

    def get_context_data(self, **kwargs):
        context = super(QuestionTagAllListView, self).get_context_data(
            **kwargs)
        if 'search' in self.request.GET:
            search_text = self.request.GET.get('search')
        else:
            search_text = ''
        context['search_text'] = search_text
        return context


class QuestionUserAllListView(ListView):
    context_object_name = 'rows'
    template_name = 'questions_answers/question_users_list.html'
    paginate_by = 2

    def get_queryset(self):
        if 'search' in self.request.GET:
            search_text = self.request.GET.get('search')
            users_all = User.objects.filter(
                username__contains=search_text).exclude(
                username='AnonymousUser')
            rows = [users_all[x:x + 4] for x in range(0, len(users_all),4)]
            return rows
        else:
            users_all = User.objects.all().exclude(username='AnonymousUser')
            rows = [users_all[x:x + 4] for x in range(0, len(users_all), 4)]
            return rows

    def get_context_data(self, **kwargs):
        context = super(QuestionUserAllListView, self).get_context_data(
            **kwargs)
        if 'search' in self.request.GET:
            search_text = self.request.GET.get('search')
        else:
            search_text = ''
        context['search_text'] = search_text
        return context


def search_tags(request):
    """Ajax-поиск тегов"""

    search_text = ''
    if request.method == 'POST':
        text = request.POST['search_text']
        if len(text) > 1:
            search_text = text
    question_tags = QuestionTag.objects.filter(name__icontains=search_text)
    rows = [question_tags[x:x + 4] for x in range(0, len(question_tags), 4)]
    paginator = Paginator(rows, 2)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        rows_search_tags = paginator.page(page)
    except (EmptyPage, InvalidPage):

        rows_search_tags = paginator.page(paginator.num_pages)
    return render_to_response('questions_answers/question_tags_search.html',
                              {'question_search_tags': question_tags,
                               'rows_search_tags': rows_search_tags,
                               'search_text': search_text})


def search_users(request):
    """Ajax-поиск пользователей"""

    search_text = ''
    if request.method == 'POST':
        text = request.POST['search_text']
        if len(text) > 1:
            search_text = text

    users_all = User.objects.filter(username__icontains=search_text).exclude(
        username='AnonymousUser')
    rows = [users_all[x:x + 4] for x in range(0, len(users_all), 4)]
    paginator = Paginator(rows, 2)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        rows_search_users = paginator.page(page)
    except (EmptyPage, InvalidPage):

        rows_search_users = paginator.page(paginator.num_pages)

    return render_to_response('questions_answers/question_users_search.html',
                              {'users_all': users_all,
                               'rows_search_users': rows_search_users,
                               'search_text': search_text})


class QuestionCommentCreateView(LoginRequiredMixin, CreateView):
    form_class = QuestionCommentForm
    template_name = 'questions_answers/question_detail.html'

    def form_valid(self, form):
        current_question = get_object_or_404(Question,
                                             slug=self.kwargs['slug'])
        instance = form.save(commit=False)
        instance.question = current_question
        instance.author = self.request.user
        instance.save()
        return HttpResponseRedirect(
            reverse('question_detail', kwargs={'slug': self.kwargs['slug']}))

    def get_context_data(self, **kwargs):
        context = super(QuestionCommentCreateView, self).get_context_data(
            **kwargs)
        current_question = get_object_or_404(Question,
                                             slug=self.kwargs['slug'])
        question_comment_form = QuestionCommentForm(self.request.POST,
                                                    instance=current_question)
        context['form'] = AnswerCreateForm(self, self.request.user,
                                           instance=current_question)
        context['question_detail'] = current_question
        context['comment_question_form'] = question_comment_form
        context['comment_answer_form'] = AnswerCommentForm(
            instance=current_question)
        return context


class AnswerCommentCreateView(LoginRequiredMixin, CreateView):
    form_class = AnswerCommentForm
    template_name = 'questions_answers/question_detail.html'

    def form_valid(self, form):
        current_answer = get_object_or_404(Answer, id=self.kwargs['id'])
        current_question = current_answer.question
        instance = form.save(commit=False)
        instance.answer = current_answer
        instance.author = self.request.user
        instance.save()
        return HttpResponseRedirect(
            reverse('question_detail', kwargs={'slug': current_question.slug}))

    def get_context_data(self, **kwargs):
        context = super(AnswerCommentCreateView, self).get_context_data(
            **kwargs)
        current_answer = get_object_or_404(Answer, id=self.kwargs['id'])
        current_question = current_answer.question
        answer_comment_form = AnswerCommentForm(self.request.POST,
                                                instance=current_answer)
        context['form'] = AnswerCreateForm(self, self.request.user,
                                           instance=current_question)
        context['question_detail'] = current_question
        context['comment_question_form'] = QuestionCommentForm(
            instance=current_question)
        context['comment_answer_form'] = answer_comment_form
        return context


def get_active_questions():
    """Показывает вопросы с недавней активностью"""

    answers = Answer.objects.all().order_by("-created_at")[:10]
    recent_answers = [a.question for a in answers]

    comments = Comment.objects.all().order_by("-added")[:10]
    recent_comments_questions = []
    for c in comments:
        if c.question is None:
            continue
        else:
            recent_comments_questions.append(c.question)
    recent_comments_answers = []
    for c in comments:
        if c.answer is None:
            continue
        else:
            recent_comments_answers.append(c.answer.question)
    active_questions = list(set(
        chain(recent_answers, recent_comments_questions,
              recent_comments_answers)))
    return active_questions[::-1]