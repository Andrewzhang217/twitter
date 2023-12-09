from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed


class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        # DO NOT put SQL query in for loops, slow
        # for follower in FriendshipService.get_follower(tweet.user):
        #     NewsFeed.objects.create(user=follower, tweet=tweet)

        # bulk create to combine into only 1 INSERT query
        newsfeed = [
            NewsFeed(user=follower, tweet=tweet)  # no save no SQL operations
            for follower in FriendshipService.get_follower(tweet.user)
        ]
        newsfeed.append(NewsFeed(user=tweet.user, tweet=tweet))  # add this tweet to his own newsfeed
        NewsFeed.objects.bulk_create(newsfeed)
