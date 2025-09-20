from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from ..models import Account, Transaction


@staff_member_required
def get_user_accounts_for_admin(request):
    """API endpoint to get filtered accounts for admin transaction forms"""
    user_id = request.GET.get('user_id')
    kind = request.GET.get('kind')
    
    if not user_id:
        return JsonResponse({'source_accounts': [], 'destination_accounts': []})
    
    # Get all accounts for the user
    user_accounts = Account.objects.filter(user_id=user_id)
    
    # For credit increase and withdrawal request, only show rial accounts
    if kind in [Transaction.KIND_CREDIT_INCREASE, Transaction.KIND_WITHDRAWAL_REQUEST]:
        rial_accounts = user_accounts.filter(account_type=Account.ACCOUNT_TYPE_RIAL)
        
        if kind == Transaction.KIND_CREDIT_INCREASE:
            # Credit increase uses destination_account
            return JsonResponse({
                'source_accounts': [],
                'destination_accounts': [
                    {'id': acc.id, 'name': acc.name, 'account_type': acc.account_type}
                    for acc in rial_accounts
                ]
            })
        elif kind == Transaction.KIND_WITHDRAWAL_REQUEST:
            # Withdrawal request uses source_account
            return JsonResponse({
                'source_accounts': [
                    {'id': acc.id, 'name': acc.name, 'account_type': acc.account_type}
                    for acc in rial_accounts
                ],
                'destination_accounts': []
            })
    
    # For other transaction types, show all user accounts
    accounts_data = [
        {'id': acc.id, 'name': acc.name, 'account_type': acc.account_type}
        for acc in user_accounts
    ]
    
    return JsonResponse({
        'source_accounts': accounts_data,
        'destination_accounts': accounts_data
    })
