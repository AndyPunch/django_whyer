from django.db import models
from django.utils import timezone


class Contact(models.Model):
    subject = models.CharField(max_length=100)
    mail = models.EmailField()
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return self.subject