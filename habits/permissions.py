from rest_framework.permissions import BasePermission, SAFE_METHODS

'''специальный класс для владельца или для всех если объект публичный и методы не изменяют его состояние'''
class IsOwnerOrPublicReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user == obj.owner:
            return True

        return obj.is_public and request.method in SAFE_METHODS
