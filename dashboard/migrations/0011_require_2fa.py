from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_business_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='require_2fa',
            field=models.BooleanField(
                default=False,
                help_text='Require all users to verify via Google Authenticator after login',
            ),
        ),
    ]
