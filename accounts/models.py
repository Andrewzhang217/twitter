from accounts.listeners import profile_changed
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_delete
from utils.listeners import invalidate_object_cache


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
    # import here to prevent cyclic dependency
    from accounts.services import UserService
    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    profile = UserService.get_profile_through_cache(user.id)
    # Use the attributes of the user object for caching to avoid repeated queries to the database
    # when calling the same user's profile multiple times.
    setattr(user, '_cached_user_profile', profile)
    return profile


User.profile = property(get_profile)

# hook up with listeners to invalidate cache
pre_delete.connect(invalidate_object_cache, sender=User)
post_save.connect(invalidate_object_cache, sender=User)

pre_delete.connect(profile_changed, sender=UserProfile)
post_save.connect(profile_changed, sender=UserProfile)
