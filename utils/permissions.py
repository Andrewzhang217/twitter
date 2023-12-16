from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    """
        check obj.user == request.user
        - For action with detail=False  ，only check has_permission
        - For action with detail=True，check has_permission and has_object_permission
        error msg will show IsObjectOwner.message
        """
    message = "You do not have permission to access this object"

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
