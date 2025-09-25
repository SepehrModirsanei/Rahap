from django.db import migrations, models
import uuid


def backfill_short_user_id(apps, schema_editor):
    User = apps.get_model('finance', 'User')
    for user in User.objects.all().iterator():
        if not getattr(user, 'short_user_id', None):
            base = str(user.user_id).replace('-', '')
            length = 8
            candidate = base[:length]
            while User.objects.filter(short_user_id=candidate).exclude(pk=user.pk).exists():
                length += 1
                if length <= 12:
                    candidate = base[:length]
                else:
                    candidate = str(uuid.uuid4()).replace('-', '')[:12]
                    break
            user.short_user_id = candidate
            user.save(update_fields=['short_user_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0032_transaction_dest_price_irr_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='short_user_id',
            field=models.CharField(db_index=True, editable=False, max_length=12, null=True, unique=True, verbose_name='Short User ID'),
        ),
        migrations.RunPython(backfill_short_user_id, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='short_user_id',
            field=models.CharField(db_index=True, editable=False, max_length=12, unique=True, verbose_name='Short User ID'),
        ),
    ]


