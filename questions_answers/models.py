from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from djangoratings.fields import VotingField

from questions_answers.utils import unique_slugify


class QuestionTag(models.Model):
    name = models.CharField(max_length=30, blank=True)
    slug = models.SlugField()

    def __unicode__(self):
        return self.name

    def save(self, **kwargs):
        slug = self.name
        unique_slugify(self, slug)
        super(QuestionTag, self).save()

    def get_absolute_url(self):
        return reverse('question_tags', kwargs={'slug': self.slug})


class Question(models.Model):
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=255)
    question_tag = models.ManyToManyField(QuestionTag, null=True, blank=True)
    question_text = models.TextField()
    author = models.ForeignKey(User)
    created_at = models.DateTimeField(default=timezone.now)
    view_count = models.BigIntegerField(default=1)
    rating = VotingField(can_change_vote=True, allow_delete=True)

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        slug = self.title
        unique_slugify(self, slug)
        super(Question, self).save()

    def get_absolute_url(self):
        return reverse('question_detail', kwargs={'slug': self.slug})


class Answer(models.Model):
    question = models.ForeignKey(Question)
    answer_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User)
    rating = VotingField(can_change_vote=True, allow_delete=True)

    #def get_absolute_url(self):
    #return u"%s#answer_%s" % (
    #self.question.get_absolute_url(),
    #self.id)

    def __unicode__(self):
        return u"id: %s question: %s text: %s " % (
            self.id, self.question, self.answer_text[:100])


class SavedQuestion(models.Model):
    user = models.ForeignKey(User)
    question = models.ForeignKey(Question)
    saved_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        unique_together = (('user', 'question'),)

    def __unicode__(self):
        return '%s %s' % (self.user, self.question.title)







