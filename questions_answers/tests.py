#-*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from models import Question, Answer, QuestionTag
from profiles.factories import *
from profiles.models import UserProfile
from questions_answers.forms import AnswerCreateForm, QuestionCreateForm, QuestionCommentForm, AnswerCommentForm


class FormTest(TestCase):
    def setUp(self):
        self.user = UserFactory(username='user', password='user')
        self.user2 = UserFactory.create()
        self.profile = UserProfile.objects.create(user=self.user)
        self.profile2 = UserProfile.objects.create(user=self.user2)
        self.question = Question.objects.create(id=1, author=self.profile.user, question_text='question_text', title='title', slug='title')
        self.answer = Answer.objects.create(id=1, question_id=1, author=self.profile2.user, answer_text='answer_text')

    def login(self):
        self.client.login(username='user', password='user')

    def test_question_form(self):
        self.login()
        question_data = {
            'title': 'title',
            'question_text': 'question_text',
            'tag': 'django'
        }
        form = QuestionCreateForm(data=question_data)
        self.assertEqual(form.is_valid(), True)
        response = self.client.get(reverse('ask_question_form'))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('ask_question_form'), question_data)
        self.assertEqual(response.status_code, 302)

    def test_question_edit_form(self):
        self.login()
        question_data = {
            'title': 'title2',
            'question_text': 'question_text2',
            'tag': 'django2'
        }
        form = QuestionCreateForm(data=question_data)
        self.assertEqual(form.is_valid(), True)
        response = self.client.get(reverse('ask_question_form'))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('ask_question_form'), question_data)
        self.assertEqual(response.status_code, 302)

    def test_answer_form(self):
        self.login()
        answer_data = {

            'answer_text': 'answer_text'
        }
        form = AnswerCreateForm(data=answer_data, author=self.user, current_question=self.question)
        self.assertEqual(form.is_valid(), True)
        response = self.client.get(reverse('add_answer', kwargs={'slug': self.question.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('add_answer', kwargs={'slug': self.question.slug}), answer_data)
        self.assertEqual(response.status_code, 302)

    def test_question_comment_form(self):
        self.login()
        question_comment_data = {

            'comment': 'question_comment_text'
            }
        form = QuestionCommentForm(data=question_comment_data)
        self.assertEqual(form.is_valid(), True)
        response = self.client.get(reverse('add_question_comment', kwargs={'slug': self.question.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('add_question_comment', kwargs={'slug': self.question.slug}), question_comment_data)
        self.assertEqual(response.status_code, 302)

    def test_answer_comment_form(self):
        self.login()
        answer_comment_data = {

            'comment': 'answer_comment_text'
            }
        form = AnswerCommentForm(data=answer_comment_data)
        self.assertEqual(form.is_valid(), True)
        response = self.client.get(reverse('add_answer_comment', kwargs={'id': self.answer.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('add_answer_comment', kwargs={'id': self.answer.id}), answer_comment_data)
        self.assertEqual(response.status_code, 302)


class ViewTest(TestCase):

    def setUp(self):
        self.user = UserFactory(username='user', password='user')
        self.profile = UserProfile.objects.create(user=self.user)
        self.question = Question.objects.create(id=1, author=self.profile.user, question_text='question_text', title='title', slug='title')
        self.answer = Answer.objects.create(id=1, question_id=1, author=self.profile.user, answer_text='answer_text')
        self.tag = QuestionTag.objects.create(id=1, name='django', slug='django')

    def login(self):
        self.client.login(username='user', password='user')

    def test_view_denies_anonymous(self):
        response = self.client.get('/ask_question_terms/')
        self.assertRedirects(response, 'accounts/login/?next=/ask_question_terms/')

    def test_view_loads(self):
        self.login()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('featured_questions'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('unanswered_questions'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('votes_questions'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('question_detail', kwargs={'slug': self.question.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('question_edit', kwargs={'slug': self.question.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('question_delete', kwargs={'slug': self.question.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('ask_question'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('ask_question_form'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('question_complete', kwargs={'slug': self.question.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('add_answer', kwargs={'slug': self.question.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('question_tags_all'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('question_users_all'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('search_tags'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('search_users'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('add_question_comment', kwargs={'slug': self.question.slug}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('add_answer_comment', kwargs={'id': self.answer.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('question_rate', kwargs={'object_id': self.question.id, 'score': 'up'}))
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse('answer_rate', kwargs={'object_id': self.answer.id, 'score': 'up'}))
        self.assertEqual(response.status_code, 302)
        response = self.client.post(reverse('question_save', kwargs={'slug': self.question.slug}))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('question_tags', kwargs={'slug': self.tag.slug }))
        self.assertEqual(response.status_code, 200)

