# memcached
FOLLOWINGS_PATTERN = 'followings:{user_id}'
# FOLLOWERS_PATTERN is not cached because usually followers data are too big, millions
# also often get stale due to frequent follow/unfollow
USER_PROFILE_PATTERN = 'userprofile:{user_id}'

# redis
USER_TWEETS_PATTERN = 'user_tweets:{user_id}'
