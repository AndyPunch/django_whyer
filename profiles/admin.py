#-*- coding:utf-8 -*-
from django.contrib import admin

from models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'reputation',)

admin.site.register(UserProfile, UserProfileAdmin)

