from django_filters.rest_framework import DjangoFilterBackend
from django.utils.decorators import method_decorator
from inbox.api.serializers import (
    NotificationSerializer,
    NotificationSerializerForUpdate,
)
from notifications.models import Notification
from ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.decorators import required_params


class NotificationViewSet(
    viewsets.GenericViewSet,
    viewsets.mixins.ListModelMixin,  # this implements a list method for queryset (with pagination)
):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)
    filterset_fields = ('unread',)  # used by viewsets.mixins.ListModelMixin

    def get_queryset(self):
        # django reverse query
        return self.request.user.notifications.all()
        # this is the same as
        # return Notification.objects.filter(recipient=self.request.user)

    @action(methods=['GET'], detail=False, url_path='unread-count')
    @method_decorator(ratelimit(key='user', rate='3/s', method='GET', block=True))
    def unread_count(self, request, *args, **kwargs):
        # without specifying url_path, default will be GET /api/notifications/unread_count/
        count = self.get_queryset().filter(unread=True).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='mark-all-as-read')
    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
    def mark_all_as_read(self, request, *args, **kwargs):
        # django Notification has index(recipient, unread)
        updated_count = self.get_queryset().filter(unread=True).update(unread=False)
        return Response({'marked_count': updated_count}, status=status.HTTP_200_OK)

    @required_params(method='POST', params=['unread'])
    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
    def update(self, request, *args, **kwargs):
        # PUT /api/notifications/1/
        """
        user can mark a notification as read or unread, overload update method
        another implementation is:
            @action(methods=['POST'], detail=True, url_path='mark-as-read')
            def mark_as_read(self, request, *args, **kwargs):
                ...
            @action(methods=['POST'], detail=True, url_path='mark-as-unread')
            def mark_as_unread(self, request, *args, **kwargs):
                ...

        """
        serializer = NotificationSerializerForUpdate(
            instance=self.get_object(),
            data=request.data,
        )
        if not serializer.is_valid():
            return Response({
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        notification = serializer.save()
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK,
        )
