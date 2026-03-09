# Authentication is handled by DMOJ's APIMiddleware (judge/middleware.py).
# It processes Authorization: Bearer <token> headers and sets request.user.
# Generate a token with: python manage.py generate_api_token <username>
