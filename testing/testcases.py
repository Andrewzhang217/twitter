from django.test import TestCase as DjangoTestcase
from django.contrib.auth.models import User
from tweets.models import Tweet


class TestCase(DjangoTestcase):

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
