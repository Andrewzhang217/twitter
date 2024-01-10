from django.core.cache import caches
from friendships.hbase_models import HBaseFollowing, HBaseFollower
from friendships.models import Friendship
from gatekeeper.models import GateKeeper
from twitter import settings
from twitter.cache import FOLLOWINGS_PATTERN

import time

cache = caches['testing'] if settings.TESTING else caches['default']


class FriendshipService(object):

    @classmethod
    def get_follower(cls, user):
        friendships = Friendship.objects.filter(
            to_user=user,
        ).prefetch_related('from_user')
        return [friendship.from_user for friendship in friendships]

    @classmethod
    def get_follower_ids(cls, to_user_id):
        friendships = Friendship.objects.filter(to_user_id=to_user_id)
        return [friendship.from_user_id for friendship in friendships]

    @classmethod
    def has_followed(cls, from_user, to_user):
        return Friendship.objects.filter(
            from_user=from_user,
            to_user=to_user,
        ).exists()

    # it checks by select count > 0

    @classmethod
    def get_following_user_id_set(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        user_id_set = cache.get(key)

        # cache hit
        if user_id_set is not None:
            return user_id_set

        # cache miss
        friendships = Friendship.objects.filter(from_user_id=from_user_id)
        user_id_set = set([
            fs.to_user_id
            for fs in friendships
        ])

        # load into memcached
        cache.set(key, user_id_set)
        return user_id_set

    # remember the cache coherence protocol implemented in CS4223?
    # MESI for invalidation and Dragon for update
    # https://github.com/Andrewzhang217/simulator
    @classmethod
    def invalidate_following_cache(cls, from_user_id):
        key = FOLLOWINGS_PATTERN.format(user_id=from_user_id)
        cache.delete(key)

        # call this method in friendships api would invalidate cache when db is
        # modified by api call, but admin modification would not trigger this

    @classmethod
    def follow(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return None

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            # create data in mysql
            return Friendship.objects.create(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
            )

        # create data in hbase
        now = int(time.time() * 1000000)
        HBaseFollower.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            created_at=now,
        )
        return HBaseFollowing.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            created_at=now,
        )
