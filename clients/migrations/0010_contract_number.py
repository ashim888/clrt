from django.db import migrations, models


def backfill_contract_numbers(apps, schema_editor):
    Contract = apps.get_model("clients", "Contract")
    # order by created_at so numbers are chronological
    for idx, contract in enumerate(Contract.objects.order_by("created_at"), start=1):
        year = contract.created_at.year
        contract.contract_number = f"CON-{year}-{idx:03d}"
        contract.save(update_fields=["contract_number"])


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0009_contract_body'),
    ]

    operations = [
        # Add without unique first so backfill can run
        migrations.AddField(
            model_name='contract',
            name='contract_number',
            field=models.CharField(blank=True, max_length=20, default=''),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_contract_numbers, migrations.RunPython.noop),
        # Now add the unique constraint
        migrations.AlterField(
            model_name='contract',
            name='contract_number',
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
    ]
