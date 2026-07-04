from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0012_sitesettings_max_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='default_quote_terms',
            field=models.TextField(
                blank=True,
                help_text='Pre-filled on every new quotation; supports "Label: text" format for bold labels on print',
            ),
        ),
    ]
