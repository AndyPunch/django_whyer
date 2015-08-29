#-*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse

from guardian.shortcuts import assign_perm

from profiles.views import UserProfileUpdateForm
from profiles.factories import UserFactory
from models import UserProfile


class FormTest(TestCase):

    def setUp(self):
        self.user = UserFactory(username='user', password='user')
        self.profile = UserProfile.objects.create(user=self.user)
        assign_perm('change_userprofile', self.user, self.profile)

    def login(self):
        self.client.login(username='user', password='user')

    def test_user_profile_form(self):
        self.login()
        profile_data = {
            'bio': 'bio_text'
        }
        form = UserProfileUpdateForm(data=profile_data)
        self.assertEqual(form.is_valid(), True)
        response = self.client.get(reverse('userprofile_update'))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('userprofile_update'), profile_data)
        self.assertEqual(response.status_code, 302)

    def test_avatar_upload(self):
        image_path = settings.MEDIA_ROOT + '/testdata/cat.jpeg'
        f = open(image_path, "r")
        response = self.client.post(reverse('avatar_upload'), {'avatar': f})
        self.assertEqual(response.status_code, 302)


class ViewTest(TestCase):

    def setUp(self):
        self.user = UserFactory(username='user', password='user')
        self.profile = UserProfile.objects.create(user=self.user)
        assign_perm('change_userprofile', self.user, self.profile)

    def login(self):
        self.client.login(username='user', password='user')

    def test_view_loads(self):
        self.login()
        response = self.client.get(reverse('user_detail', kwargs={'username': self.profile.user}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('userprofile_update'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('avatar_upload'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('avatar_delete', kwargs={'pk': self.profile.id}))
        self.assertEqual(response.status_code, 200)






