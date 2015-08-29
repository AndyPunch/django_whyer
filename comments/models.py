from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from djangoratings.fields import VotingField

from questions_answers.models import Question, Answer


class Comment(models.Model):
    question = models.ForeignKey(Question, null=True, blank=True)
    answer = models.ForeignKey(Answer, null=True, blank=True)
    author = models.ForeignKey(User)
    comment = models.TextField()
    added = models.DateTimeField(default=timezone.now)
    rating = VotingField(can_change_vote=True, allow_delete=True)











