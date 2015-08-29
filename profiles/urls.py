from django.conf.urls import url, patterns

from views import MyProfileView, UserInfoView, UserProfileUpdateView
from views import AvatarUploadView, AvatarDeleteView, UserProfileDeleteView

urlpatterns = patterns('',
                       url(r'^$', MyProfileView.as_view(), name='my_profile'),
                       url(r'^(?P<username>[\w.@+-]+)/info/$',
                           UserInfoView.as_view(), name='user_detail'),
                       url(r'^accounts/settings/info/$',
                           UserProfileUpdateView.as_view(),
                           name='userprofile_update'),
                       url(r'^accounts/avatar_upload/$',
                           AvatarUploadView.as_view(), name='avatar_upload'),
                       url(r'^(?P<pk>\d+)/avatar_delete/$',
                           AvatarDeleteView.as_view(), name="avatar_delete"),
                       url(r'^(?P<pk>\d+)/profile_delete/$',
                           UserProfileDeleteView.as_view(),
                           name="profile_delete"),
                       )