from comments.api.permissions import IsObjectOwner
from comments.models import Comment
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate,
)


class CommentViewSet(viewsets.GenericViewSet):
    """
        Only implement list, create, update, destroy methods
        NO retrieve (query single comment），since no such demand
        """
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
    filterset_fields = ('tweet_id',)

    def get_permissions(self):
        # Use AllowAny() / IsAuthenticated() to instantiate
        # instead of Class name AllowAny / IsAuthenticated
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['update', 'destroy']:
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]

    def list(self, request, *args, **kwargs):
        if 'tweet_id' not in request.query_params:
            return Response(
                {
                    'message': 'missing tweet_id in request',
                    'success': False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = self.get_queryset()
        comments = self.filter_queryset(queryset) \
            .prefetch_related('user') \
            .order_by('created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(
            {'comments': serializer.data},
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }
        # Must use 'data=' to specify data passed
        # since default first param is instance
        serializer = CommentSerializerForCreate(data=data)
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # save will call the create() method of serializer to instantiate
        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        serializer = CommentSerializerForUpdate(
            instance=comment,
            data=request.data
        )
        if not serializer.is_valid():
            return Response({
                'message': 'Please check input',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return Response({'success': True}, status=status.HTTP_200_OK)
