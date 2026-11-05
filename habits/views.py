from django.db.models import Q
from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import Habit
from .pagination import HabitPageNumberPagination
from .permissions import IsOwnerOrPublicReadOnly
from .serializers import HabitFullSerializer

class HabitViewSet(ModelViewSet):
    serializer_class = HabitFullSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrPublicReadOnly]
    pagination_class = HabitPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        '''объекты текущего пользователя и публичные'''
        return Habit.objects.filter(
            Q(owner=user)|Q(is_public=True)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
