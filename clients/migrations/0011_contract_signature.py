import uuid
from django.db import migrations, models


def backfill_sign_tokens(apps, schema_editor):
    Contract = apps.get_model("clients", "Contract")
    for contract in Contract.objects.filter(sign_token__isnull=True):
        contract.sign_token = uuid.uuid4()
        contract.save(update_fields=["sign_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0010_contract_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="sign_token",
            field=models.UUIDField(null=True, blank=True, editable=False),
        ),
        migrations.RunPython(backfill_sign_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="contract",
            name="sign_token",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AddField(
            model_name="contract",
            name="signature_name",
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name="contract",
            name="signature_ip",
            field=models.GenericIPAddressField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="contract",
            name="signature_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="contract",
            name="signature_data",
            field=models.TextField(blank=True),
        ),
    ]
