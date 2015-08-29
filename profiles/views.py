#-*- coding: utf-8 -*-
from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.generic import DetailView, UpdateView, DeleteView, FormView, RedirectView

from braces.views import SetHeadlineMixin
from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin

from questions_answers.models import SavedQuestion, Question, Answer
from forms import UserUpdateForm, UserProfileUpdateForm, UserAvatarForm
from models import UserProfile


class UserInfoView(LoginRequiredMixin, DetailView):
    context_object_name = 'userinfo'
    template_name = 'profiles/user_detail.html'
    model = User

    def get_object(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return user

    def get_context_data(self, **kwargs):
        context = super(UserInfoView, self).get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.kwargs['username'])
        userprofile = get_object_or_404(UserProfile, user=user)
        questions = Question.objects.filter(author__username=user).order_by(
            '-created_at')
        answers = Answer.objects.filter(author__username=user)
        saved_questions = SavedQuestion.objects.filter(user=user)
        context['questions'] = questions
        context['answers'] = answers
        context['userprofile'] = userprofile
        context['saved_questions'] = saved_questions
        return context


class UserInfoMixin(object):
    def get_context_data(self, **kwargs):
        context = super(UserInfoMixin, self).get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.kwargs['username'])
        context['userinfo'] = user
        return context


class AvatarUploadView(LoginRequiredMixin, FormView):
    form_class = UserAvatarForm
    template_name = 'profiles/avatar_upload.html'

    def form_valid(self, form):
        user = get_object_or_404(User, username=self.request.user)
        userprofile = get_object_or_404(UserProfile, user=user)
        avatar = form.cleaned_data['avatar']

        # Удаляет старый файл в момент загрузки нового
        if userprofile.avatar != avatar:
            userprofile.avatar.delete(save=False)

        userprofile.avatar = avatar
        userprofile.save()
        return HttpResponseRedirect(
            reverse('user_detail', kwargs={'username': user}))

    def get_context_data(self, **kwargs):
        context = super(AvatarUploadView, self).get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.request.user)
        userprofile = get_object_or_404(UserProfile, user=user)
        context['userprofile'] = userprofile
        return context


class AvatarDeleteView(DeleteView):
    model = UserProfile
    success_url = reverse_lazy('avatar_upload')
    template_name = 'profiles/avatar_delete.html'

    def get_object(self):
        """Проверяем принадлежит ли объект request юзеру"""

        obj = super(AvatarDeleteView, self).get_object()
        if not obj.user == self.request.user:
            raise Http404
        avatar = obj.avatar
        return avatar


class MyProfileView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        user = self.request.user
        return reverse('user_detail', kwargs={'username': user.username})


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                     SetHeadlineMixin, UpdateView):
    form_class = UserUpdateForm
    model = User
    headline = "Изменить e-mail..."
    template_name = 'profiles/user_form.html'
    permission_required = 'auth.change_user'
    return_403 = True

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, 'Ваш электронный адрес изменён')
        return reverse_lazy('user_update')


class UserProfileUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                            SetHeadlineMixin, UpdateView):
    form_class = UserProfileUpdateForm
    model = UserProfile
    template_name = 'profiles/user_form.html'
    headline = "Изменить профиль..."
    permission_required = 'profiles.change_userprofile'
    return_403 = True

    def get_object(self):
        return self.request.user.userprofile

    def get_success_url(self):
        messages.success(self.request, 'Ваш профайл изменён')
        return reverse_lazy('userprofile_update')


class UserProfileDeleteView(PermissionRequiredMixin, DeleteView):
    model = UserProfile
    success_url = reverse_lazy('question_list')
    template_name = 'profiles/userprofile_delete.html'
    permission_required = 'profiles.delete_userprofile'
    return_403 = True

    def get_object(self):
        obj = super(UserProfileDeleteView, self).get_object()
        if not obj.user == self.request.user:
            raise Http404
        profile = obj
        return profile