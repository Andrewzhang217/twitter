def user_changed(sender, instance, **kwargs):
    # import here to prevent cyclic dependency
    from accounts.services import UserService
    UserService.invalidate_user(instance.id)


def profile_changed(sender, instance, **kwargs):
    # import here to prevent cyclic dependency
    from accounts.services import UserService
    UserService.invalidate_profile(instance.user_id)
    # key of UserProfile is user_id
