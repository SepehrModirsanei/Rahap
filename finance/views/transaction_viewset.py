from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
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

    @action(detail=True, methods=['post'], url_path='comment')
    def add_comment(self, request, pk=None):
        txn = self.get_object()
        comment = request.data.get('comment', '').strip()
        if not comment:
            return Response({'detail': 'comment is required'}, status=status.HTTP_400_BAD_REQUEST)
        txn.user_comment = comment
        txn.save(update_fields=['user_comment'])
        return Response({'detail': 'comment saved', 'transaction_code': txn.transaction_code, 'user_comment': txn.user_comment})
