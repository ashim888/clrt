from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0011_require_2fa'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='max_discount_percent',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=5,
                help_text='Maximum discount % allowed on any quotation or invoice (0 = no limit)',
            ),
        ),
    ]
