#-*- coding: utf-8 -*-
from django import forms
from django.forms import EmailInput

from models import Contact


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['subject', 'mail', 'text']

        labels = {
            'subject': 'Тема сообщения:', 'mail': 'Ваш e-mail для ответа:',
            'text': 'Текст сообщения:'
        }

        widgets = {
            'mail': EmailInput(),

        }

    def __init__(self, user, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.user = user
        try:
            email = self.user.email
            self.fields['mail'].widget.attrs[
                "value"] = email  # Вставляем email юзера в поле 'mail'
        except AttributeError:  # Например, если это анонимный юзер
            pass
