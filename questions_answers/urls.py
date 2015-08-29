from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from views import QuestionListView, QuestionDetailView, QuestionUpdateView
from views import QuestionCreateView, question_complete, AnswerCreateView
from views import rate_question, rate_answer, QuestionTagListView
from views import QuestionUserAllListView, search_tags, search_users
from views import AnswerCommentCreateView, QuestionDeleteView, QuestionSaveView
from views import QuestionTagAllListView, QuestionCommentCreateView

urlpatterns = patterns('',
                       url(r'^$', QuestionListView.as_view(),
                           name='question_list'),
                       url(r'^featured_questions/$',
                           QuestionListView.as_view(),
                           name='featured_questions'),
                       url(r'^unanswered_questions/$',
                           QuestionListView.as_view(),
                           name='unanswered_questions'),
                       url(r'^votes_questions/$', QuestionListView.as_view(),
                           name='votes_questions'),
                       url(r'^question/(?P<slug>[-\w]+)/$',
                           QuestionDetailView.as_view(),
                           name='question_detail'),
                       url(r'^question_edit/(?P<slug>[-\w]+)/$',
                           QuestionUpdateView.as_view(), name='question_edit'),
                       url(r'^question_delete/(?P<slug>[-\w]+)/$',
                           QuestionDeleteView.as_view(),
                           name="question_delete"),
                       url(r'^ask_question_terms/$', login_required(
                           TemplateView.as_view(
                               template_name='questions_answers/ask_question.html')),
                           name='ask_question'),
                       url(r'^ask_question_form/$',
                           QuestionCreateView.as_view(),
                           name='ask_question_form'),
                       url(r'^question_complete/(?P<slug>[-\w]+)/$',
                           question_complete, name='question_complete'),
                       url(r'^add_answer/(?P<slug>[-\w]+)/$',
                           AnswerCreateView.as_view(), name='add_answer'),
                       url(r'^question/(?P<slug>[-\w]+)/save/$',
                           QuestionSaveView.as_view(), name='question_save'),
                       url(
                           r'^rate_question/(?P<object_id>\d+)/(?P<score>\w+)/$',
                           rate_question, name='question_rate'),
                       url(r'^rate_answer/(?P<object_id>\d+)/(?P<score>\w+)/$',
                           rate_answer, name='answer_rate'),
                       url(r'^question_tags/(?P<slug>[-\w]+)/$',
                           QuestionTagListView.as_view(),
                           name='question_tags'),
                       url(r'^question_tags_all/$',
                           QuestionTagAllListView.as_view(),
                           name='question_tags_all'),
                       url(r'^question_users_all/$',
                           QuestionUserAllListView.as_view(),
                           name='question_users_all'),
                       url(r'^search_tags/$', search_tags, name='search_tags'),
                       url(r'^search_users/$', search_users,
                           name='search_users'),
                       url(r'^add_question_comment/(?P<slug>[-\w]+)/$',
                           QuestionCommentCreateView.as_view(),
                           name='add_question_comment'),
                       url(r'^add_answer_comment/(?P<id>\d+)/$',
                           AnswerCommentCreateView.as_view(),
                           name='add_answer_comment'),
)
