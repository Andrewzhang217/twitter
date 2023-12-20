from accounts.services import UserService
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from likes.models import Like
from tweets.constants import TweetPhotoStatus, TWEET_PHOTO_STATUS_CHOICES
from utils import time_helpers


class Tweet(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="who posts this tweet",
    )
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

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
        return UserService.get_user_through_cache(self.user_id)


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
