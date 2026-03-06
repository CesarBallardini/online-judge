from django.urls import path

from . import views

urlpatterns = [
    path('load-students/', views.LoadStudentsView.as_view(), name='api-load-students'),
    path('load-teachers/', views.LoadTeachersView.as_view(), name='api-load-teachers'),
    path('load-problems/', views.LoadProblemsView.as_view(), name='api-load-problems'),
]
