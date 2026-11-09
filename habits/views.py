from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Habit
from .pagination import HabitPageNumberPagination
from .permissions import IsOwnerOrPublicReadOnly
from .serializers import HabitFullSerializer

class HabitViewSet(ModelViewSet):
    serializer_class = HabitFullSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrPublicReadOnly]
    pagination_class = HabitPageNumberPagination

    def get_queryset(self):
        if self.action == 'list':
            return Habit.objects.filter(owner=self.request.user)

        return Habit.objects.filter(
            Q(owner=self.request.user) | Q(is_public=True)
        ).distinct()

    @action(detail=False, methods=['get'], url_path='public')
    def public_habits(self, request):
        habits = Habit.objects.filter(is_public=True)

        page = self.paginate_queryset(habits)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(habits, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
