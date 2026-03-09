from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    """Allow access only to staff users (authenticated via DMOJ Bearer token).

    DMOJ's APIMiddleware sets the user on the underlying Django request,
    so we check request._request.user rather than DRF's request.user.
    """

    def has_permission(self, request, view):
        user = getattr(request, '_request', request).user
        return (
            user is not None
            and user.is_authenticated
            and user.is_staff
        )
