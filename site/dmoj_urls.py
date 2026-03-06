from django.urls import include, path
from dmoj.urls import urlpatterns as dmoj_urlpatterns
from dmoj.urls import handler403, handler404, handler500  # noqa: F401 -- used by Django

urlpatterns = [
    path('api/admin/', include('custom_commands.urls')),
] + dmoj_urlpatterns
