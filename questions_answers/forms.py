#-*- coding: utf-8 -*-
from django import forms
from django.forms import Textarea

from models import Question, Answer
from comments.models import Comment


class QuestionCreateForm(forms.ModelForm):
    tag = forms.CharField(max_length=100, required=False, label="Теги:",
                          help_text="Укажите здесь несколько тегов через  запятую или пробел")


    class Meta:
        model = Question
        exclude = ['author', 'slug', 'created_at', 'view_count',
                   'question_tag']

        labels = {
            'title': 'Заголовок:', 'question_text': 'Текст вопроса:'
        }


class AnswerCreateForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']

        labels = {
            'answer_text': '',
        }

        widgets = {
            'answer_text': Textarea(
                attrs={'class': 'myredactor', 'rows': 3, }),

        }

    def __init__(self, author, current_question, *args, **kwargs):
        super(AnswerCreateForm, self).__init__(*args, **kwargs)
        self.author = author
        self.question = current_question

    def clean(self):
        # Чтобы юзер мог ответить на конкретный вопрос не более одного раза

        if Answer.objects.filter(question=self.question, author=self.author):
            raise forms.ValidationError("Вы уже отвечали на этот вопрос.")
        return self.cleaned_data


class QuestionCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']

        widgets = {
            'comment': Textarea(attrs={'class': 'myredactor', 'rows': 3,
                                       'placeholder': 'Присоединиться к обсуждению...'}),

        }

        labels = {
            'comment': 'Комментарии:',
        }


class AnswerCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']

        widgets = {
            'comment': Textarea(attrs={'class': 'myredactor', 'rows': 3,
                                       'placeholder': 'Присоединиться к обсуждению...'}),
        }

        labels = {
            'comment': 'Комментарии:',
        }


