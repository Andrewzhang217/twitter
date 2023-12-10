from django.test import TestCase as DjangoTestcase
from django.contrib.auth.models import User
from tweets.models import Tweet
from comments.models import Comment
from rest_framework.test import APIClient


class TestCase(DjangoTestcase):

    @property
    def anonymous_client(self):
        # instance-level cache (inside each TestCase instance)
        if hasattr(self, '_anonymous_client'):
            return self._anonymous_client
        self._anonymous_client = APIClient()
        return self._anonymous_client

    def create_user(self, username, email=None, password=None):
        if password is None:
            password = 'default password'

        if email is None:
            email = f'{username}@gmail.com'

        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'

        return Tweet.objects.create(user=user, content=content)

    def create_comment(self, user, tweet, content=None):
        if content is None:
            content = "default comment content"

        return Comment.objects.create(user=user, tweet=tweet, content=content)
