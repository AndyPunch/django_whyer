#-*- coding: utf-8 -*-
from time import time
from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.validators import MaxLengthValidator

from questions_answers.models import Question, Answer


def get_upload_file_name(instance, filename):
    return "uploads/avatars/%s_%s" % (str(time()).replace('.', '_'), filename)


def get_reputation():
    questions_list = Question.objects.values_list('author_id',
                                                  'rating_score').order_by('author')
    # список юзеров задававших вопросы
    u_q = [i[0] for i in questions_list]

    # список юзеров задававших вопросы без повторов юзеров
    questions_authors = set(u_q)

    reputation_from_questions = dict.fromkeys(questions_authors, 0)
    for i in questions_list:
        for key in reputation_from_questions:
            if i[0] == key:
                # словарь, где ключ -id юзера, значение сумма его рейтинга за вопросы
                reputation_from_questions[key] += i[1]

    answers_list = Answer.objects.values_list('author_id',
                                              'rating_score').order_by('author')
    # список юзеров дававших ответы
    u_a = [i[0] for i in answers_list]

    # список юзеров дававших ответы без повторов юзеров
    answers_authors = set(u_a)

    reputation_from_answers = dict.fromkeys(answers_authors, 0)

    # здесь получаем словарь пользователь: рейтинг(вопросы и ответы)
    reputation_from_answers.update(reputation_from_questions)

    for i in answers_list:
        for key in reputation_from_answers:
            if i[0] == key:

                # словарь, где ключ -id юзера, значение-сумма его рейтинга за ответы
                reputation_from_answers[key] += i[1]

    reputation = reputation_from_answers
    return reputation


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    bio = models.TextField(blank=True, validators=[MaxLengthValidator(1000)],
                           help_text='Не более 1000 символов')
    website = models.URLField(blank=True)
    avatar = models.ImageField(null=True, blank=True,
                               upload_to=get_upload_file_name)
    reputation = models.IntegerField(default=0)

    def __unicode__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse('user_detail', kwargs={'username': self.user.username})


#SIGNALS

from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from guardian.shortcuts import assign_perm
from django.db.models.signals import post_save


@receiver(user_signed_up)
def new_user_signup(sender, user, request, **kwargs):
    user_profile = UserProfile.objects.get_or_create(user=user)[0]
    assign_perm('change_userprofile', user, user_profile)
    assign_perm('delete_userprofile', user, user_profile)
    assign_perm('change_user', user, user)


@receiver(post_save, sender=Question)
def get_score_question(sender, instance, **kwargs):
    """Получаем сигнал при изменении таблицы с вопросами,
    сверяем и если нужно обновляем рейтинг пользователя

    """
    user_id = instance.author_id

    # словарь юзер: рейтинг(вопросы и ответы)
    reputation = get_reputation()

    if user_id in reputation.keys():
        userprofile = UserProfile.objects.get(user_id=user_id)
        userprofile.reputation = reputation[user_id]
        userprofile.save()


@receiver(post_save, sender=Answer)
def get_score_answer(sender, instance, **kwargs):
    """Получаем сигнал при изменении таблицы с ответами ,
    сверяем и если нужно обновляем рейтинг пользователя

    """
    user_id = instance.author_id
    reputation = get_reputation()
    if user_id in reputation.keys():
        userprofile = UserProfile.objects.get(user_id=user_id)
        userprofile.reputation = reputation[user_id]
        userprofile.save()


def delete_user(sender, instance=None, **kwargs):
    try:
        instance.user
    except User.DoesNotExist:
        pass
    else:
        instance.user.delete()


signals.post_delete.connect(delete_user, sender=UserProfile)





