from celery import shared_task
from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from tweets.models import Tweet
from utils.time_constants import ONE_HOUR


@shared_task(time_limit=ONE_HOUR)
def fanout_newsfeeds_task(tweet_id):
    # prevent cyclic dependency
    from newsfeeds.services import NewsFeedService

    # DO NOT put SQL query in for loops, slow
    # for follower in FriendshipService.get_follower(tweet.user):
    #     NewsFeed.objects.create(user=follower, tweet=tweet)

    # bulk create to combine into only 1 INSERT query
    tweet = Tweet.objects.get(id=tweet_id)
    newsfeeds = [
        NewsFeed(user=follower, tweet=tweet)  # no save no SQL operations
        for follower in FriendshipService.get_follower(tweet.user)
    ]
    newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))  # add this tweet to his own newsfeed
    NewsFeed.objects.bulk_create(newsfeeds)

    # bulk create does NOT trigger post_save signal
    # manually push into cache
    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)
