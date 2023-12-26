from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from newsfeeds.listeners import push_newsfeed_to_cache
from tweets.models import Tweet
from utils.memcached_helper import MemcachedHelper


class NewsFeed(models.Model):
    # user is who can see this tweet
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    # need this because cannot sort using created_at field from other tables
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('user', 'created_at'),)
        unique_together = (('user', 'tweet'),)
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.created_at} inbox of {self.user} : {self.tweet}'

    @property
    def cached_tweet(self):
        return MemcachedHelper.get_object_through_cache(Tweet, self.tweet_id)


# bulk_create in fanout does NOT call this, handled in services
post_save.connect(push_newsfeed_to_cache, sender=NewsFeed)
