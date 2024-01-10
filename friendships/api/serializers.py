from accounts.api.serializers import UserSerializerForFriendships
from accounts.services import UserService
from django.contrib.auth.models import User
from friendships.services import FriendshipService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class BaseFriendshipSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    has_followed = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def following_user_id_set(self):
        if self.context['request'].user.is_anonymous:
            return {}
        # cached in the current process
        if hasattr(self, '_cached_following_user_id_set'):
            return self._cached_following_user_id_set
        user_id_set = FriendshipService.get_following_user_id_set(
            self.context['request'].user.id,
        )
        setattr(self, '_cached_following_user_id_set', user_id_set)
        return user_id_set

    # must be implemented in subclasses
    def get_user_id(self, obj):
        raise NotImplementedError

    def get_user(self, obj):
        user = UserService.get_user_by_id(self.get_user_id(obj))
        return UserSerializerForFriendships(user).data

    def get_created_at(self, obj):
        return obj.created_at

    def get_has_followed(self, obj):
        return self.get_user_id(obj) in self.following_user_id_set()


class FollowerSerializer(BaseFriendshipSerializer):
    def get_user_id(self, obj):
        return obj.from_user_id


class FollowingSerializer(BaseFriendshipSerializer):
    def get_user_id(self, obj):
        return obj.to_user_id


class FriendshipSerializerForCreate(serializers.Serializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

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
        return FriendshipService.follow(
            from_user_id=validated_data['from_user_id'],
            to_user_id=validated_data['to_user_id']
        )

    def update(self, instance, validated_data):
        pass
