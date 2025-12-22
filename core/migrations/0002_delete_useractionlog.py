from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_user_activity"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UserActionLog",
        ),
    ]
