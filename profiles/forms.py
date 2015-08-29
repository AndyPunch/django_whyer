#-*- coding: utf-8 -*-
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.core.files.images import get_image_dimensions

from models import UserProfile


class UserUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = ('email',)


class UserProfileUpdateForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ('website', 'bio',)
        labels = {'website': 'Мой вебсайт/блог:', 'bio': 'О себе:'}


class UserAvatarForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar',)

        labels = {'avatar': ''}

    def __init__(self, *args, **kwargs):
        super(UserAvatarForm, self).__init__(*args, **kwargs)
        # Переопределяем поле не изменяя модели.
        self.fields['avatar'].required = True

    def clean_avatar(self):
        # Получаем данные из нужного поля.
        avatar = self.cleaned_data['avatar']

        try:
        # Проверяем размеры изображения.
        # Получаем размеры загружаемого изображения.
            w, h = get_image_dimensions(avatar)

            # Задаем ограничения размеров.
            max_width = 600
            max_height = 600

            # Собственно сравнение.
            if w > max_width or h > max_height:
                raise forms.ValidationError(
                    'Максимальный размер загружаемого файла %s x %s пикселей.' % (
                    max_height, max_width))

            # Не пропускаем файлы, размер (вес) которых более 100 килобайт.
            if len(avatar) > (100 * 1024):
                raise forms.ValidationError(
                    'Аватар не может юыть более 100 кб.')

        except AttributeError:
            pass

        return avatar
