from rest_framework import viewsets, permissions
from ..models import Transaction
from ..serializers import TransactionSerializer


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if hasattr(obj, 'user'):
            return obj.user == user
        return False


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        txn = serializer.save(user=self.request.user)
        txn.apply()
