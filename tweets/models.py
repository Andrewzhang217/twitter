from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save, pre_delete
from likes.models import Like
from tweets.constants import TweetPhotoStatus, TWEET_PHOTO_STATUS_CHOICES
from tweets.listeners import push_tweet_to_cache
from utils import time_helpers
from utils.listeners import invalidate_object_cache
from utils.memcached_helper import MemcachedHelper


class Tweet(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="who posts this tweet",
    )
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    # newly added field MUST set null=True，otherwise would iterate through the whole table to set default = 0
    # Migration would be slow，locking the whole table，user cannot create new tweets
    likes_count = models.IntegerField(default=0, null=True)
    comments_count = models.IntegerField(default=0, null=True)

    class Meta:
        index_together = (('user', 'created_at'),)
        ordering = ('user', '-created_at')
        # ordering does not modify the database, specifies the order of django queryset

    def __str__(self):
        # this would be shown when print the instance
        return f'{self.created_at} {self.user}: {self.content}'

    @property
    def hours_to_now(self):
        return (time_helpers.utc_now() - self.created_at).seconds // 3600

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Tweet),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)


class TweetPhoto(models.Model):
    # photo under which tweet
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)

    # who upload this photo, Although this info can be obtained from tweets, but repeated records in TweetPhoto can be
    # convenient. For example, if a person often uploads some illegal photos, then the newly uploaded photos by this
    # user can be marked as the focus of review. Or when we need to ban all photos uploaded by a user,
    # we can quickly filter through this model.
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    # image file
    file = models.FileField()
    order = models.IntegerField(default=0)  # order of photos under a tweet

    # image status, for review
    status = models.IntegerField(
        default=TweetPhotoStatus.PENDING,
        choices=TWEET_PHOTO_STATUS_CHOICES,
    )

    # soft delete
    # When a photo is deleted, it will first be marked as deleted and will not be actually deleted immediately.
    # The purpose of this is that if the true deletion is performed immediately when the tweet is deleted,
    # it will usually take some time and affect efficiency.
    # Can use asynchronous tasks to slowly perform deletion in the background.
    has_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            ('tweet', 'order'),
            ('user', 'created_at'),
            ('has_deleted', 'created_at'),
            ('status', 'created_at'),
        )

    def __str__(self):
        return f'{self.tweet_id}: {self.file}'


pre_delete.connect(invalidate_object_cache, sender=Tweet)
post_save.connect(invalidate_object_cache, sender=Tweet)
post_save.connect(push_tweet_to_cache, sender=Tweet)

# Now does not support modify tweets, if user_id 1 has [{1, 'hello}, {2, world] tweets in redis
# modification of tweets does not update cache in redis
# a possible solution is to only store tweets ids in redis, then get tweets contents from memcached
# cache.get_many([...])
