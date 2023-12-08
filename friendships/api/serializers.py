from accounts.api.serializers import UserSerializerForFriendships
from rest_framework.exceptions import ValidationError
from friendships.models import Friendship
from rest_framework import serializers
from django.contrib.auth.models import User


class FollowerSerializer(serializers.ModelSerializer):
    # can access a field or method of a model instance through source=xxx
    # i.e. model_instance.xxx
    user = UserSerializerForFriendships(source='from_user')

    class Meta:
        model = Friendship
        fields = ('user', 'created_at')


class FollowingSerializer(serializers.ModelSerializer):
    user = UserSerializerForFriendships(source='to_user')

    class Meta:
        model = Friendship
        fields = ('user', 'created_at')


class FriendshipSerializerForCreate(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ('from_user_id', 'to_user_id')

    def validate(self, attrs):
        if attrs['from_user_id'] == attrs['to_user_id']:
            raise ValidationError({
                'message': 'You cannot follow yourself.'
            })
        if not User.objects.filter(id=attrs['to_user_id']).exists():
            raise ValidationError({
                'message': 'You cannot follow a user who does not exist',
            })

        return attrs

    def create(self, validated_data):
        return Friendship.objects.create(
            from_user_id=validated_data['from_user_id'],
            to_user_id=validated_data['to_user_id']
        )
