from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper


class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        # DO NOT put SQL query in for loops, slow
        # for follower in FriendshipService.get_follower(tweet.user):
        #     NewsFeed.objects.create(user=follower, tweet=tweet)

        # bulk create to combine into only 1 INSERT query
        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)  # no save no SQL operations
            for follower in FriendshipService.get_follower(tweet.user)
        ]
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))  # add this tweet to his own newsfeed
        NewsFeed.objects.bulk_create(newsfeeds)

        # bulk create does NOT trigger post_save signal
        # manually push into cache
        for newsfeed in newsfeeds:
            cls.push_newsfeed_to_cache(newsfeed)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        # Lazy evaluation
        queryset = NewsFeed.objects.filter(user_id=user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id).order_by('-created_at')
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        RedisHelper.push_object(key, newsfeed, queryset)
