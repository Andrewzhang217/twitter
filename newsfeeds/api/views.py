from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from newsfeeds.models import NewsFeed
from newsfeeds.api.serializers import NewsFeedSerializer
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    def get_queryset(self):
        # custom queryset, need auth to see newsfeed
        # only can see newsfeed where user=current logged in user
        # also can be self.request.user.newsfeed_set.all()
        return NewsFeed.objects.filter(user=self.request.user)

    def list(self, request):
        query_set = self.paginate_queryset(self.get_queryset())
        serializer = NewsFeedSerializer(
            query_set,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)
