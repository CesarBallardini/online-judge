from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class AdminAPIKeyAuthentication(BaseAuthentication):
    """
    Authenticate requests using a static API key from settings.
    Header: Authorization: Bearer <ADMIN_API_KEY>
    """

    keyword = 'Bearer'

    def authenticate(self, request):
        api_key = getattr(settings, 'ADMIN_API_KEY', None)
        if not api_key:
            raise AuthenticationFailed('ADMIN_API_KEY is not configured on the server.')

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            return None  # No auth header -- let other authenticators try

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]
        if token != api_key:
            raise AuthenticationFailed('Invalid API key.')

        # Return a tuple of (user, auth_info). user=None since this is a service key.
        # Views that need a user object can use request.auth to verify the key was valid.
        return (None, token)
