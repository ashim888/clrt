from django.db import migrations, models


def migrate_is_done_to_status(apps, schema_editor):
    Activity = apps.get_model("leads", "Activity")
    Activity.objects.filter(is_done=True).update(status="completed")
    Activity.objects.filter(is_done=False).update(status="pending")


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0003_activity_resolution_note"),
    ]

    operations = [
        # 1. Add new status field (default pending)
        migrations.AddField(
            model_name="activity",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("completed", "Completed"),
                    ("cancelled", "Cancelled"),
                    ("rescheduled", "Rescheduled"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        # 2. Copy boolean → status
        migrations.RunPython(migrate_is_done_to_status, migrations.RunPython.noop),
        # 3. Drop is_done
        migrations.RemoveField(
            model_name="activity",
            name="is_done",
        ),
    ]
