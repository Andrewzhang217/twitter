from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    # OneToOneField creates a unique index，make sure no more than
    # 1 UserProfile points to a User
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    avatar = models.FileField(null=True)
    # when a user is created，a user profile object also created
    # now nickname is not set yet，so null=True
    nickname = models.CharField(null=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.user, self.nickname)


# Define a profile property method and implant it into the User model, so that when we access the profile
# through an instance of user, user_instance.profile will perform get_or_create in UserProfile
# to obtain the corresponding profile object. The writing method is actually a method of hacking using the
# flexibility of Python, which will facilitate us to quickly access the corresponding profile information
# through the user.
def get_profile(user):
    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    # Use the attributes of the user object for caching to avoid repeated queries to the database
    # when calling the same user's profile multiple times.
    setattr(user, '_cached_user_profile', profile)
    return profile


User.profile = property(get_profile)
