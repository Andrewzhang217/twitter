from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id',
            'actor_content_type',
            'actor_object_id',
            'verb',
            'action_object_content_type',
            'action_object_object_id',
            'target_content_type',
            'target_object_id',
            'timestamp',
            'unread',
        )


class NotificationSerializerForUpdate(serializers.ModelSerializer):
    # BooleanField compatible with true, false, "true", "false", "True", "1", "0"
    # and convert to True / False in python
    unread = serializers.BooleanField()

    class Meta:
        model = Notification
        fields = ('unread',)

    def update(self, instance, validated_data):
        instance.unread = validated_data['unread']
        instance.save()
        return instance
