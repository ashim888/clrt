import uuid
from django.db import migrations, models


def backfill_sign_tokens(apps, schema_editor):
    Quote = apps.get_model("proposals", "Quote")
    for quote in Quote.objects.filter(sign_token__isnull=True):
        quote.sign_token = uuid.uuid4()
        quote.save(update_fields=["sign_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("proposals", "0003_quote_timestamps"),
    ]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="sign_token",
            field=models.UUIDField(null=True, blank=True, editable=False),
        ),
        migrations.RunPython(backfill_sign_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="quote",
            name="sign_token",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.AddField(
            model_name="quote",
            name="signature_name",
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name="quote",
            name="signature_ip",
            field=models.GenericIPAddressField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="quote",
            name="signature_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="quote",
            name="signature_data",
            field=models.TextField(blank=True),
        ),
    ]
