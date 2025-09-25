from django.db import migrations, models


def backfill_snapshot_numbers(apps, schema_editor):
    AccountDailyBalance = apps.get_model('finance', 'AccountDailyBalance')
    DepositDailyBalance = apps.get_model('finance', 'DepositDailyBalance')

    # Per account, order by snapshot_date asc and assign 1..N
    for account_id in AccountDailyBalance.objects.values_list('account_id', flat=True).distinct():
        qs = AccountDailyBalance.objects.filter(account_id=account_id).order_by('snapshot_date', 'id')
        num = 1
        for rec in qs:
            rec.snapshot_number = num
            rec.save(update_fields=['snapshot_number'])
            num += 1

    # Per deposit
    for deposit_id in DepositDailyBalance.objects.values_list('deposit_id', flat=True).distinct():
        qs = DepositDailyBalance.objects.filter(deposit_id=deposit_id).order_by('snapshot_date', 'id')
        num = 1
        for rec in qs:
            rec.snapshot_number = num
            rec.save(update_fields=['snapshot_number'])
            num += 1


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0033_user_short_user_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountdailybalance',
            name='snapshot_number',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='depositdailybalance',
            name='snapshot_number',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(backfill_snapshot_numbers, migrations.RunPython.noop),
    ]


