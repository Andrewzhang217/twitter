from newsfeeds.services import NewsFeedService
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import TweetSerializer, TweetSerializerForCreate, TweetSerializerForDetail
from tweets.models import Tweet
from tweets.services import TweetService
from utils.decorators import required_params
from utils.paginations import EndlessPagination


class TweetViewSet(viewsets.GenericViewSet):
    serializer_class = TweetSerializerForCreate
    queryset = Tweet.objects.all()
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    # retrieve a specific tweet
    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()
        serializer = TweetSerializerForDetail(
            tweet,
            context={'request': request},
        )
        return Response(serializer.data)

    @required_params(params=['user_id'])
    def list(self, request, *args, **kwargs):
        # select * from twitter_tweets
        # where user_id = xxx
        # order by created_at desc
        # this SQL query uses composite index (user, created_at)
        user_id = request.query_params['user_id']
        # tweets = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
        # now can try to get cached tweets in redis
        tweets = TweetService.get_cached_tweets(user_id)
        tweets = self.paginate_queryset(tweets)
        serializer = TweetSerializer(
            tweets,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    def create(self, request):

        serializer = TweetSerializerForCreate(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input",
                "errors": serializer.errors
            }, status=400)

        # save will call the create() in TweetSerializerForCreate
        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        return Response(
            TweetSerializer(tweet, context={'request': request}).data,
            status=201)
