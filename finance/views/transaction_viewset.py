from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from ..services.quote_service import QuoteService
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

    @action(detail=False, methods=['post'], url_path='quote')
    def quote(self, request):
        """
        Preview destination_amount for an intended account-to-account transfer.
        Expected payload: { amount, source_account_type, destination_account_type }
        """
        try:
            amount = float(request.data.get('amount'))
        except Exception:
            return Response({'detail': 'amount is required and must be numeric'}, status=status.HTTP_400_BAD_REQUEST)

        src_type = request.data.get('source_account_type')
        dst_type = request.data.get('destination_account_type')
        if not src_type or not dst_type:
            return Response({'detail': 'source_account_type and destination_account_type are required'}, status=status.HTTP_400_BAD_REQUEST)

        quote = QuoteService.compute_destination_amount(amount, src_type, dst_type)
        if quote.get('destination_amount') is None:
            return Response({'detail': 'quote unavailable for given inputs'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({
            'destination_amount': quote['destination_amount'],
            'exchange_rate': quote.get('exchange_rate'),
            'source_price_irr': quote.get('source_price_irr'),
            'dest_price_irr': quote.get('dest_price_irr'),
        })
