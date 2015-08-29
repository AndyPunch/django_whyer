from django.contrib import admin

from django_summernote.admin import SummernoteModelAdmin

from models import Comment


class CommentAdmin(SummernoteModelAdmin):
    list_display = ('added', "question", "answer")

admin.site.register(Comment, CommentAdmin)



