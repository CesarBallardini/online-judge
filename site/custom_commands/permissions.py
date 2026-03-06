from rest_framework.permissions import BasePermission


class HasValidAPIKey(BasePermission):
    """Allow access only when a valid API key was provided."""

    def has_permission(self, request, view):
        return request.auth is not None
