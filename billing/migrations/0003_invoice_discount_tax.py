from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_recurring_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='discount_percent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='invoice',
            name='tax_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='amount',
            field=models.DecimalField(decimal_places=2, help_text='Subtotal before discount and tax', max_digits=12),
        ),
    ]
