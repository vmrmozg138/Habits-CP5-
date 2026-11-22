from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import User
from .serializers import TelegramChatIdSerializer, UserSerializer


class RegisterAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class TelegramChatIdUpdateAPIView(UpdateAPIView):
    serializer_class = TelegramChatIdSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
