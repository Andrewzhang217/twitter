from django.contrib.auth.models import User
from django.db import models
from utils import time_helpers


class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('user', 'created_at'),)
        ordering = ('user', '-created_at')
        # ordering does not modify the database, specifies the order of django queryset

    @property
    def hours_to_now(self):
        return (time_helpers.utc_now() - self.created_at).seconds // 3600

    def __str__(self):
        # this would be shown when print the instance
        return f'{self.created_at} {self.user}: {self.content}'