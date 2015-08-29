from django.contrib import admin

from django_summernote.admin import SummernoteModelAdmin

from models import Question, Answer, SavedQuestion, QuestionTag


class QuestionAdmin(SummernoteModelAdmin):
    list_display = ('title', 'author', 'created_at', 'view_count',)
    prepopulated_fields = {'slug': ('title',)}


class AnswerAdmin(SummernoteModelAdmin):
    pass


class SavedQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question',)


class QuestionTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(SavedQuestion, SavedQuestionAdmin)
admin.site.register(QuestionTag, QuestionTagAdmin)
