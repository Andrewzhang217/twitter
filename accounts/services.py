from accounts.models import UserProfile
from django.contrib.auth.models import User
from django.core.cache import caches
from twitter.cache import USER_PATTERN, USER_PROFILE_PATTERN
from twitter.settings import TESTING

cache = caches['testing'] if TESTING else caches['default']


class UserService:

    @classmethod
    def get_user_through_cache(cls, user_id):
        key = USER_PATTERN.format(user_id=user_id)

        # read from cache
        user = cache.get(key)

        # cache hit return
        if user is not None:
            return user

        # cache miss, load from db
        try:
            user = User.objects.get(id=user_id)
            cache.set(key, user)
        except User.DoesNotExist:
            user = None
        return user

    @classmethod
    def invalidate_user(cls, user_id):
        key = USER_PATTERN.format(user_id=user_id)
        cache.delete(key)

    @classmethod
    def get_profile_through_cache(cls, user_id):
        key = USER_PROFILE_PATTERN.format(user_id=user_id)

        # read from cache first
        profile = cache.get(key)
        # cache hit return
        if profile is not None:
            return profile

        # cache miss, read from db
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        cache.set(key, profile)
        return profile

    @classmethod
    def invalidate_profile(cls, user_id):
        key = USER_PROFILE_PATTERN.format(user_id=user_id)
        cache.delete(key)
