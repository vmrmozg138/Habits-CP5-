from django.urls import path

from .apps import UsersConfig
from .views import RegisterAPIView, TelegramChatIdUpdateAPIView

app_name = UsersConfig.name

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path(
        "telegram/",
        TelegramChatIdUpdateAPIView.as_view(),
        name="telegram_update",
    ),
]
