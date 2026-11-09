from django.urls import path
from rest_framework.urls import app_name

from .views import RegisterAPIView
from .apps import UsersConfig

app_name = UsersConfig.name

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
]