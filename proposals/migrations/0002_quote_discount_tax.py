from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='quote',
            name='discount_percent',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='quote',
            name='tax_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
